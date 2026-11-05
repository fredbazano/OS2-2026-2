#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <sys/mman.h>
#include <semaphore.h>
#include "mandelbrot.h"

// Fila de trabalho em memória compartilhada entre os processos.
// A "fila" é só o índice da próxima linha ainda não calculada.
typedef struct {
    sem_t sem_lock;   // semáforo POSIX compartilhado (pshared=1), protege next_row
    int next_row;     // próxima linha livre (região crítica)
} SharedState;

static void printUsage(const char *progName) {
    fprintf(stderr, "Uso: %s <num_processos> [arquivo_saida] [factor]\n", progName);
    fprintf(stderr, "Exemplo: %s 4 image_proc.ppm 480\n", progName);
    fprintf(stderr, "Parâmetros:\n");
    fprintf(stderr, "  <num_processos> : Quantidade de processos a serem criados (obrigatório, ex: 2, 4, 8)\n");
    fprintf(stderr, "  [arquivo_saida] : Nome do arquivo PPM gerado (padrão: image.ppm)\n");
    fprintf(stderr, "  [factor]        : Escala da resolução (16*factor x 9*factor, padrão: 480 -> 7680x4320)\n");
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
    int factor = FACTOR_PADRAO;

    if (argc >= 3) {
        outputFile = argv[2];
    }
    if (argc >= 4) {
        factor = parseFactor(argv[3]);
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

    // 1. Memória Compartilhada (mmap com MAP_SHARED | MAP_ANONYMOUS), criada ANTES do fork.
    // Os filhos herdam o mapeamento: escrevem direto nos pixels e o pai grava a imagem depois.
    // Sem MAP_SHARED, cada filho escreveria numa cópia própria (copy-on-write).
    Color *frameBuffer = mmap(NULL, fb_size, PROT_READ | PROT_WRITE, MAP_SHARED | MAP_ANONYMOUS, -1, 0);
    if (frameBuffer == MAP_FAILED) {
        perror("Falha ao alocar memória compartilhada para o framebuffer (mmap)");
        return 1;
    }

    // A fila de trabalho e o semáforo também precisam estar em memória compartilhada
    SharedState *shared = mmap(NULL, sizeof(SharedState), PROT_READ | PROT_WRITE, MAP_SHARED | MAP_ANONYMOUS, -1, 0);
    if (shared == MAP_FAILED) {
        perror("Falha ao alocar memória compartilhada para SharedState (mmap)");
        munmap(frameBuffer, fb_size);
        return 1;
    }

    // pshared=1: semáforo compartilhado entre processos; valor inicial 1 (exclusão mútua)
    if (sem_init(&shared->sem_lock, 1, 1) != 0) {
        perror("Falha ao inicializar semáforo compartilhado (sem_init)");
        munmap(shared, sizeof(SharedState));
        munmap(frameBuffer, fb_size);
        return 1;
    }
    shared->next_row = 0;

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
            // Divisão dinâmica: cada processo pega a próxima linha livre ao terminar a anterior.
            // Linhas que cruzam o conjunto (até 1500 iterações por pixel) custam muito mais
            // que linhas da borda; assim, quem pega linhas leves simplesmente pega mais linhas.
            for (;;) {
                // Região Crítica: retirar uma linha da fila
                sem_wait(&shared->sem_lock);
                int y = shared->next_row++;
                sem_post(&shared->sem_lock);

                if (y >= height) {
                    break; // fila vazia
                }

                // Cada linha pertence a um único processo: escrita no framebuffer sem lock
                renderRow(frameBuffer, y, width, height);
            }

            // _exit (e não exit) para não descarregar de novo o buffer de stdout herdado do pai
            _exit(0);
        }
    }

    // ==========================================
    // CÓDIGO DO PROCESSO PAI
    // ==========================================
    // Sincronização: O processo pai aguarda a conclusão de todos os processos filhos
    for (int p = 0; p < num_processes; p++) {
        if (waitpid(pids[p], NULL, 0) < 0) {
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
