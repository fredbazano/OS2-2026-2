#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include "mandelbrot.h"

// Fila de trabalho compartilhada por todas as threads.
// A "fila" é só o índice da próxima linha ainda não calculada.
typedef struct {
    int next_row;            // próxima linha livre (região crítica)
    pthread_mutex_t mutex;   // protege next_row
    int width;
    int height;
    Color *frameBuffer;      // compartilhado: threads usam o mesmo espaço de endereçamento
} WorkQueue;

static void *threadWorker(void *arg) {
    WorkQueue *q = (WorkQueue *)arg;

    // Divisão dinâmica: cada thread pega a próxima linha livre ao terminar a anterior.
    // Linhas que cruzam o conjunto (até 1500 iterações por pixel) custam muito mais
    // que linhas da borda; assim, quem pega linhas leves simplesmente pega mais linhas.
    for (;;) {
        // Região Crítica: retirar uma linha da fila
        pthread_mutex_lock(&q->mutex);
        int y = q->next_row++;
        pthread_mutex_unlock(&q->mutex);

        if (y >= q->height) {
            break; // fila vazia
        }

        // Cada linha pertence a uma única thread: escrita no framebuffer sem lock
        renderRow(q->frameBuffer, y, q->width, q->height);
    }

    return NULL;
}

static void printUsage(const char *progName) {
    fprintf(stderr, "Uso: %s <num_threads> [arquivo_saida] [factor]\n", progName);
    fprintf(stderr, "Exemplo: %s 4 image_threads.ppm 480\n", progName);
    fprintf(stderr, "Parâmetros:\n");
    fprintf(stderr, "  <num_threads>   : Quantidade de threads a serem criadas (obrigatório, ex: 2, 4, 8)\n");
    fprintf(stderr, "  [arquivo_saida] : Nome do arquivo PPM gerado (padrão: image.ppm)\n");
    fprintf(stderr, "  [factor]        : Escala da resolução (16*factor x 9*factor, padrão: 480 -> 7680x4320)\n");
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
    printf("     Mandelbrot PPM - MÚLTIPLAS THREADS \n");
    printf("========================================\n");
    printf("Threads trabalhadoras  : %d\n", num_threads);
    printf("Resolução              : %dx%d (factor=%d)\n", width, height, factor);
    printf("Arquivo de saída       : %s\n", outputFile);
    printf("Tamanho do framebuffer : %.2f MB\n", (double)fb_size / (1024.0 * 1024.0));

    Color *frameBuffer = malloc(fb_size);
    pthread_t *threads = malloc((size_t)num_threads * sizeof(pthread_t));
    if (!frameBuffer || !threads) {
        fprintf(stderr, "Erro ao alocar memória.\n");
        return 1;
    }

    WorkQueue queue;
    queue.next_row = 0;
    queue.width = width;
    queue.height = height;
    queue.frameBuffer = frameBuffer;
    pthread_mutex_init(&queue.mutex, NULL);

    // Medição do tempo de cálculo
    double t_calc_start = getTimeSec();

    for (int t = 0; t < num_threads; t++) {
        if (pthread_create(&threads[t], NULL, threadWorker, &queue) != 0) {
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
    printf("Tempo de Cálculo (Computacional): %.6f s\n", compTime);
    printf("Tempo de Gravação (I/O)        : %.6f s\n", ioTime);
    printf("Tempo Total                    : %.6f s\n", totalTime);
    printf("------------------------------\n");

    pthread_mutex_destroy(&queue.mutex);
    free(threads);
    free(frameBuffer);

    return 0;
}
