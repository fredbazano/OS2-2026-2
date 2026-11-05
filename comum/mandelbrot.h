#ifndef MANDELBROT_H
#define MANDELBROT_H

// Funções comuns às três versões (sequencial, processos e threads).
// O cálculo de cada pixel é idêntico em todas. Só muda quem calcula cada linha.

#define FACTOR_PADRAO 480   // 16*480 x 9*480 = 7680x4320 (8K)
#define MAX_ITERATIONS 1000

typedef struct {
    unsigned char r;
    unsigned char g;
    unsigned char b;
} __attribute__((packed)) Color;

// Calcula a cor de um pixel (até MAX_ITERATIONS iterações de z = z² + c).
Color pixelShader(int x, int y, int width, int height);

// Calcula todos os pixels da linha y e grava no framebuffer.
// É a unidade de trabalho distribuída entre processos/threads.
void renderRow(Color *frameBuffer, int y, int width, int height);

// Grava o framebuffer em um arquivo PPM binário (P6).
void writeImage(Color *frameBuffer, int width, int height, const char *outputFile);

// Tempo monotônico em segundos (para medir cálculo e I/O).
double getTimeSec(void);

// Converte o argumento [factor]; retorna FACTOR_PADRAO se for inválido.
int parseFactor(const char *arg);

#endif
