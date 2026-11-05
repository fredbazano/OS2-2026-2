#include <stdio.h>
#include <stdlib.h>
#include "mandelbrot.h"

int main(int argc, char *argv[]) {
    // Parâmetros opcionais por linha de comando:
    // ./sequencial [arquivo_saida] [factor]
    const char *outputFile = "image.ppm";
    int factor = FACTOR_PADRAO;

    if (argc >= 2) {
        outputFile = argv[1];
    }
    if (argc >= 3) {
        factor = parseFactor(argv[2]);
    }

    int width = 16 * factor;
    int height = 9 * factor;

    printf("========================================\n");
    printf("   Mandelbrot PPM - Versão SEQUENCIAL   \n");
    printf("========================================\n");
    printf("Resolução: %dx%d (factor=%d)\n", width, height, factor);
    printf("Arquivo de saída: %s\n", outputFile);

    Color *frameBuffer = malloc((size_t)width * height * sizeof(Color));
    if (!frameBuffer) {
        fprintf(stderr, "Erro ao alocar memória para o framebuffer.\n");
        return 1;
    }

    // Medição do tempo de cálculo (computacional)
    double t_calc_start = getTimeSec();

    // Um único fluxo calcula todas as linhas, de cima para baixo
    for (int y = 0; y < height; y++) {
        renderRow(frameBuffer, y, width, height);
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

    free(frameBuffer);
    return 0;
}
