#include <stdio.h>
#include <stdlib.h>
#include <math.h>

typedef struct {
    unsigned char r;
    unsigned char g;
    unsigned char b;
} Color;

double clamp(double f) {
    return fmin(fmax(f, 0.0), 1.0);
}

Color colorf(double r, double g, double b) {
    r = clamp(r);
    g = clamp(g);
    b = clamp(b);
    return (Color){
        r * 255,
        g * 255,
        b * 255
    };
}

Color pixelShader(int x, int y, int width, int height) {
    double aspectRatio = (double) width / height;

    //inverte o eixo y
    y = height - y;

    //panning horizontal
    x = x - width / 8;

    // normalização de 0 a 1
    double u = ((double) (x)  / width);
    double v = ((double)y / height);

    // normalização de -1 a 1, com correção de aspect ratio e zoom
    double nx = (((2.0f * u) - 1.0f) * aspectRatio) * 1.2;
    double ny = ((2.0f * v) - 1.0f) * 1.2;

    int maxIterations = 1500;
    //double squaredEscapeRadius = 8.0;
    double escapeRadius = 4.0;

    double cx = 0;
    double cy = 0;

    for (int i = 0; i < maxIterations; i++) {
        double temp_x = cx * cx - cy * cy + nx;
        double temp_y = 2 * cx * cy + ny;
        cx = temp_x;
        cy = temp_y;

        //double squaredDistance = cx * cx + cy * cy;
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
    fprintf(file, "P6\n");
    fprintf(file, "%d %d\n", width, height);
    fprintf(file, "255\n");

    for (int i=0; i < width * height; i++) {
        fputc(frameBuffer[i].r, file);
        fputc(frameBuffer[i].g, file);
        fputc(frameBuffer[i].b, file);
    }

    fclose(file);
    printf("Wrote %s\n", outputFile);
}

int main() {
    int factor = 120;
    int width = 16 * factor;
    int height = 9 * factor;

    Color *frameBuffer = malloc(width * height * sizeof(Color));

    int index = 0;
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            frameBuffer[index++] = pixelShader(x, y, width, height);
        }
    }
    writeImage(frameBuffer, width, height, "image.ppm");
    return 0;
}

 