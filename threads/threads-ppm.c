#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#include <pthread.h>

typedef struct {
    unsigned char r;
    unsigned char g;
    unsigned char b;
} __attribute__((packed)) Color;

typedef struct {
    int thread_id;
    int num_threads;
    int width;
    int height;
    Color *frameBuffer;
    pthread_mutex_t *mutex;
    long long *total_iterations;
} ThreadData;

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

static void *threadWorker(void *arg) {
    ThreadData *data = (ThreadData *)arg;
    long long local_iterations = 0;

    // Divisão de trabalho intercalada (Round-Robin) entre as threads
    for (int y = data->thread_id; y < data->height; y += data->num_threads) {
        int rowOffset = y * data->width;
        for (int x = 0; x < data->width; x++) {
            int iters = 0;
            data->frameBuffer[rowOffset + x] = pixelShader(x, y, data->width, data->height, &iters);
            local_iterations += iters;
        }
    }

    // Região Crítica: atualização protegida por Mutex das iterações globais
    pthread_mutex_lock(data->mutex);
    *(data->total_iterations) += local_iterations;
    pthread_mutex_unlock(data->mutex);

    return NULL;
}

static void printUsage(const char *progName) {
    fprintf(stderr, "Uso: %s <num_threads> [arquivo_saida] [factor]\n", progName);
    fprintf(stderr, "Exemplo: %s 4 image_threads.ppm 120\n", progName);
    fprintf(stderr, "Parâmetros:\n");
    fprintf(stderr, "  <num_threads>   : Quantidade de threads a serem criadas (obrigatório, ex: 2, 4, 8)\n");
    fprintf(stderr, "  [arquivo_saida] : Nome do arquivo PPM gerado (padrão: image.ppm)\n");
    fprintf(stderr, "  [factor]        : Escala da resolução (16*factor x 9*factor, padrão: 120 -> 1920x1080)\n");
}

int main(int argc, char *argv[]) {
    if (argc < 2) {
        printUsage(argv[0]);
        return 1;
    }

    int num_threads = atoi(argv[1]);
    if (num_threads <= 0) {
        fprintf(stderr, "Erro: O número de threads deve ser maior que 0.\n");
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
    printf("     Mandelbrot PPM - MÚLTIPLAS THREADS \n");
    printf("========================================\n");
    printf("Threads trabalhadoras  : %d\n", num_threads);
    printf("Resolução              : %dx%d (factor=%d)\n", width, height, factor);
    printf("Arquivo de saída       : %s\n", outputFile);
    printf("Tamanho do framebuffer : %.2f MB\n", (double)fb_size / (1024.0 * 1024.0));

    Color *frameBuffer = malloc(fb_size);
    if (!frameBuffer) {
        fprintf(stderr, "Erro ao alocar memória para o framebuffer.\n");
        return 1;
    }

    pthread_t *threads = malloc((size_t)num_threads * sizeof(pthread_t));
    ThreadData *threadData = malloc((size_t)num_threads * sizeof(ThreadData));
    pthread_mutex_t mutex;
    pthread_mutex_init(&mutex, NULL);
    long long total_iterations = 0;

    // Medição do tempo de cálculo
    double t_calc_start = getTimeSec();

    for (int t = 0; t < num_threads; t++) {
        threadData[t].thread_id = t;
        threadData[t].num_threads = num_threads;
        threadData[t].width = width;
        threadData[t].height = height;
        threadData[t].frameBuffer = frameBuffer;
        threadData[t].mutex = &mutex;
        threadData[t].total_iterations = &total_iterations;

        if (pthread_create(&threads[t], NULL, threadWorker, &threadData[t]) != 0) {
            perror("Erro ao criar thread");
            return 1;
        }
    }

    // Sincronização: aguarda o término de todas as threads
    for (int t = 0; t < num_threads; t++) {
        pthread_join(threads[t], NULL);
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
    printf("Total de iterações calculadas  : %lld\n", total_iterations);
    printf("Tempo de Cálculo (Computacional): %.6f s\n", compTime);
    printf("Tempo de Gravação (I/O)        : %.6f s\n", ioTime);
    printf("Tempo Total                    : %.6f s\n", totalTime);
    printf("------------------------------\n");

    pthread_mutex_destroy(&mutex);
    free(threads);
    free(threadData);
    free(frameBuffer);

    return 0;
}

