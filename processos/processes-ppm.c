#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <sys/mman.h>
#include <semaphore.h>
#include <fcntl.h>
#include <errno.h>

typedef struct {
    unsigned char r;
    unsigned char g;
    unsigned char b;
} __attribute__((packed)) Color;

// Estrutura em memória compartilhada para sincronização e estatísticas
typedef struct {
    sem_t sem_lock;              // Semáforo POSIX compartilhado para proteção da região crítica
    long long total_iterations;  // Contador acumulado de iterações do fractal
    int workers_completed;       // Número de processos que completaram sua fatia
} SharedState;

static inline double clamp(double f) {
    return fmin(fmax(f, 0.0), 1.0);
}

static inline Color colorf(double r, double g, double b) {
    r = clamp(r);
    g = clamp(g);
    b = clamp(b);
    Color c;
    c.r = (unsigned char)(r * 255.0);
    c.g = (unsigned char)(g * 255.0);
    c.b = (unsigned char)(b * 255.0);
    return c;
}

static inline Color pixelShader(int x, int y, int width, int height, int *iterations_out) {
    double aspectRatio = (double) width / height;

    // inverte o eixo y
    y = height - y;

    // panning horizontal
    x = x - width / 8;

    // normalização de 0 a 1
    double u = ((double) x / width);
    double v = ((double) y / height);

    // normalização de -1 a 1, com correção de aspect ratio e zoom
    double nx = (((2.0f * u) - 1.0f) * aspectRatio) * 1.2;
    double ny = ((2.0f * v) - 1.0f) * 1.2;

    int maxIterations = 1500;
    double escapeRadius = 4.0;

    double cx = 0;
    double cy = 0;

    for (int i = 0; i < maxIterations; i++) {
        double temp_x = cx * cx - cy * cy + nx;
        double temp_y = 2 * cx * cy + ny;
        cx = temp_x;
        cy = temp_y;

        double distance = sqrt(cx * cx + cy * cy);
        if (distance > escapeRadius) {
            double smooth = i + 1.0 - log2(log2(sqrt(distance)));
            double t = clamp(smooth / 100.0);
            if (iterations_out) *iterations_out = i + 1;
            return colorf(t, t, t);
        }
    }
    if (iterations_out) *iterations_out = maxIterations;
    return colorf(0.0, 0.0, 0.0);
}

void writeImage(Color *frameBuffer, int width, int height, const char *outputFile) {
    FILE *file = fopen(outputFile, "wb");
    if (!file) {
        perror("Erro ao abrir arquivo para escrita");
        return;
    }
    fprintf(file, "P6\n");
    fprintf(file, "%d %d\n", width, height);
    fprintf(file, "255\n");

    size_t totalPixels = (size_t)width * height;
    size_t written = fwrite(frameBuffer, sizeof(Color), totalPixels, file);
    if (written != totalPixels) {
        fprintf(stderr, "Aviso: gravados %zu de %zu pixels.\n", written, totalPixels);
    }

    fclose(file);
    printf("[IO] Imagem salva em: %s (%dx%d pixels)\n", outputFile, width, height);
}

static double getTimeSec(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec * 1e-9;
}

static void printUsage(const char *progName) {
    fprintf(stderr, "Uso: %s <num_processos> [arquivo_saida] [factor]\n", progName);
    fprintf(stderr, "Exemplo: %s 4 image_proc.ppm 120\n", progName);
    fprintf(stderr, "Parâmetros:\n");
    fprintf(stderr, "  <num_processos> : Quantidade de processos a serem criados (obrigatório, ex: 2, 4, 8)\n");
    fprintf(stderr, "  [arquivo_saida] : Nome do arquivo PPM gerado (padrão: image.ppm)\n");
    fprintf(stderr, "  [factor]        : Escala da resolução (16*factor x 9*factor, padrão: 120 -> 1920x1080)\n");
}

int main(int argc, char *argv[]) {
    if (argc < 2) {
        printUsage(argv[0]);
        return 1;
    }

    int num_processes = atoi(argv[1]);
    if (num_processes <= 0) {
        fprintf(stderr, "Erro: O número de processos deve ser maior que 0.\n");
        return 1;
    }

    const char *outputFile = "image.ppm";
    int factor = 480;

    if (argc >= 3) {
        outputFile = argv[2];
    }
    if (argc >= 4) {
        factor = atoi(argv[3]);
        if (factor <= 0) {
            fprintf(stderr, "Fator inválido. Usando valor padrão: 480\n");
            factor = 480;
        }
    }

    int width = 16 * factor;
    int height = 9 * factor;
    size_t fb_size = (size_t)width * height * sizeof(Color);

    printf("========================================\n");
    printf("    Mandelbrot PPM - MÚLTIPLOS PROCESSOS\n");
    printf("========================================\n");
    printf("Processos trabalhadores: %d\n", num_processes);
    printf("Resolução              : %dx%d (factor=%d)\n", width, height, factor);
    printf("Arquivo de saída       : %s\n", outputFile);
    printf("Tamanho do framebuffer : %.2f MB\n", (double)fb_size / (1024.0 * 1024.0));

    // 1. Alocação de Memória Compartilhada (POSIX mmap com MAP_SHARED | MAP_ANONYMOUS)
    // O framebuffer compartilhado permite que os processos filhos escrevam diretamente
    // nos pixels da imagem, e o processo pai possa salvá-lo após a sincronização.
    Color *frameBuffer = mmap(NULL, fb_size, PROT_READ | PROT_WRITE,
                              MAP_SHARED | MAP_ANONYMOUS, -1, 0);
    if (frameBuffer == MAP_FAILED) {
        perror("Falha ao alocar memória compartilhada para o framebuffer (mmap)");
        return 1;
    }

    // Estrutura de controle e sincronização compartilhada
    SharedState *shared = mmap(NULL, sizeof(SharedState), PROT_READ | PROT_WRITE,
                               MAP_SHARED | MAP_ANONYMOUS, -1, 0);
    if (shared == MAP_FAILED) {
        perror("Falha ao alocar memória compartilhada para SharedState (mmap)");
        munmap(frameBuffer, fb_size);
        return 1;
    }

    // Inicialização do semáforo com pshared=1 (compartilhado entre processos)
    if (sem_init(&shared->sem_lock, 1, 1) != 0) {
        perror("Falha ao inicializar semáforo compartilhado (sem_init)");
        munmap(shared, sizeof(SharedState));
        munmap(frameBuffer, fb_size);
        return 1;
    }
    shared->total_iterations = 0;
    shared->workers_completed = 0;

    pid_t *pids = malloc((size_t)num_processes * sizeof(pid_t));
    if (!pids) {
        perror("Falha ao alocar array de PIDs");
        sem_destroy(&shared->sem_lock);
        munmap(shared, sizeof(SharedState));
        munmap(frameBuffer, fb_size);
        return 1;
    }

    // Início da medição de tempo de cálculo (computacional)
    double t_calc_start = getTimeSec();

    // 2. Criação dos processos com fork()
    for (int p = 0; p < num_processes; p++) {
        pids[p] = fork();

        if (pids[p] < 0) {
            perror("Erro ao executar fork()");
            // Aguarda os processos já criados para evitar processos zumbis
            for (int k = 0; k < p; k++) {
                waitpid(pids[k], NULL, 0);
            }
            free(pids);
            sem_destroy(&shared->sem_lock);
            munmap(shared, sizeof(SharedState));
            munmap(frameBuffer, fb_size);
            return 1;
        }

        if (pids[p] == 0) {
            // ==========================================
            // CÓDIGO DO PROCESSO FILHO (Worker p)
            // ==========================================
            long long local_iterations = 0;

            // Estratégia de Divisão de Trabalho: Linhas Intercaladas (Round-Robin)
            // Cada processo 'p' processa as linhas y onde (y % num_processes) == p.
            // Isso garante um balanceamento de carga perfeito, pois as linhas do centro
            // (que exigem o número máximo de iterações) são uniformemente distribuídas.
            for (int y = p; y < height; y += num_processes) {
                int rowOffset = y * width;
                for (int x = 0; x < width; x++) {
                    int iters = 0;
                    frameBuffer[rowOffset + x] = pixelShader(x, y, width, height, &iters);
                    local_iterations += iters;
                }
            }

            // Região Crítica: Atualização atômica das estatísticas compartilhadas
            // Protegida pelo semáforo compartilhado entre processos
            sem_wait(&shared->sem_lock);
            shared->total_iterations += local_iterations;
            shared->workers_completed++;
            sem_post(&shared->sem_lock);

            // Libera a memória compartilhada no processo filho antes de sair
            munmap(shared, sizeof(SharedState));
            munmap(frameBuffer, fb_size);
            free(pids);

            _exit(0); // Encerra o processo filho
        }
    }

    // ==========================================
    // CÓDIGO DO PROCESSO PAI
    // ==========================================
    // Sincronização: O processo pai aguarda a conclusão de todos os processos filhos
    for (int p = 0; p < num_processes; p++) {
        int status;
        pid_t wpid = waitpid(pids[p], &status, 0);
        if (wpid < 0) {
            perror("Erro em waitpid");
        }
    }

    double t_calc_end = getTimeSec();
    double compTime = t_calc_end - t_calc_start;

    // Medição do tempo de gravação I/O
    double t_io_start = getTimeSec();
    writeImage(frameBuffer, width, height, outputFile);
    double t_io_end = getTimeSec();
    double ioTime = t_io_end - t_io_start;

    double totalTime = compTime + ioTime;

    printf("\n--- Métricas de Desempenho ---\n");
    printf("Processos finalizados          : %d / %d\n", shared->workers_completed, num_processes);
    printf("Total de iterações calculadas  : %lld\n", shared->total_iterations);
    printf("Tempo de Cálculo (Computacional): %.6f s\n", compTime);
    printf("Tempo de Gravação (I/O)        : %.6f s\n", ioTime);
    printf("Tempo Total                    : %.6f s\n", totalTime);
    printf("------------------------------\n");

    // Liberação de recursos no processo pai
    free(pids);
    sem_destroy(&shared->sem_lock);
    munmap(shared, sizeof(SharedState));
    munmap(frameBuffer, fb_size);

    return 0;
}

