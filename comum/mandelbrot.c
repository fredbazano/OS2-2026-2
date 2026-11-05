#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#include "mandelbrot.h"

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

Color pixelShader(int x, int y, int width, int height) {
    double aspectRatio = (double) width / height;

    // inverte o eixo y
    y = height - y;

    // panning horizontal
    x = x - width / 8;

    // normalização de 0 a 1
    double u = ((double) x / width);
    double v = ((double) y / height);

    // normalização de -1 a 1, com correção de aspect ratio e zoom
    // c = cx + cy·i: o ponto do plano complexo correspondente a este pixel
    double cx = (((2.0f * u) - 1.0f) * aspectRatio) * 1.2;
    double cy = ((2.0f * v) - 1.0f) * 1.2;

    // raio de escape 2 (padrão do Mandelbrot): |z| > 2 garante divergência.
    // Compara o quadrado da distância com o quadrado do raio (2² = 4) e evita um sqrt por iteração.
    double squaredEscapeRadius = 4.0;

    // z = zx + zy·i: o valor iterado, começa em 0
    double zx = 0;
    double zy = 0;

    for (int i = 0; i < MAX_ITERATIONS; i++) {
        // z = z² + c, com números complexos: (zx + zy·i)² = (zx² - zy²) + (2·zx·zy)·i
        double temp_zx = zx * zx - zy * zy + cx;   // parte real
        double temp_zy = 2 * zx * zy + cy;         // parte imaginária
        
        // temporárias: zy precisa do zx antigo, então só atualiza depois de calcular os dois
        zx = temp_zx;
        zy = temp_zy;

        double squaredDistance = zx * zx + zy * zy;
        if (squaredDistance > squaredEscapeRadius) {
            // coloração suave: i + 1 - log2(log2|z|), com |z| = sqrt(squaredDistance).
            // Esse sqrt roda uma vez por pixel (só quando escapa), não por iteração.
            double smooth = i + 1.0 - log2(log2(sqrt(squaredDistance)));
            double t = smooth / 100.0;   // colorf já aplica o clamp
            return colorf(t, t, t);
        }
    }
    return colorf(0.0, 0.0, 0.0);
}

void renderRow(Color *frameBuffer, int y, int width, int height) {
    Color *row = frameBuffer + (size_t)y * width;
    for (int x = 0; x < width; x++) {
        row[x] = pixelShader(x, y, width, height);
    }
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

double getTimeSec(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec * 1e-9;
}

int parseFactor(const char *arg) {
    int factor = atoi(arg);
    if (factor <= 0) {
        fprintf(stderr, "Fator inválido. Usando valor padrão: %d\n", FACTOR_PADRAO);
        factor = FACTOR_PADRAO;
    }
    return factor;
}
