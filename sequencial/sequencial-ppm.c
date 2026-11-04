#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

typedef struct {
    unsigned char r;
    unsigned char g;
    unsigned char b;
} __attribute__((packed)) Color;

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

static inline Color pixelShader(int x, int y, int width, int height) {
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
            return colorf(t, t, t);
        }
    }
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

int main(int argc, char *argv[]) {
    // Parâmetros opcionais por linha de comando:
    // ./sequencial [arquivo_saida] [factor]
    const char *outputFile = "image.ppm";
    int factor = 480;

    if (argc >= 2) {
        outputFile = argv[1];
    }
    if (argc >= 3) {
        factor = atoi(argv[2]);
        if (factor <= 0) {
            fprintf(stderr, "Fator inválido. Usando valor padrão: 480\n");
            factor = 480;
        }
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

    int index = 0;
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            frameBuffer[index++] = pixelShader(x, y, width, height);
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

    free(frameBuffer);
    return 0;
}

