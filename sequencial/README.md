# Mandelbrot - Versão Sequencial

Esta pasta contém a implementação sequencial do gerador de fractal de Mandelbrot em formato de imagem PPM (P6).

## Código-fonte
- `sequencial-ppm.c`: Código em C puro com cálculo iterativo dos pontos do fractal de Mandelbrot e medição de tempo de execução (computacional vs I/O).

## Compilação
A partir da raiz do projeto:
```bash
make bin/sequencial
```
Ou manualmente com `gcc`:
```bash
gcc -O3 -Wall sequencial/sequencial-ppm.c -o bin/sequencial -lm
```

## Execução
```bash
./bin/sequencial [arquivo_saida] [factor]
```
- `arquivo_saida` (opcional): Nome do arquivo `.ppm` gerado (padrão: `image.ppm`).
- `[factor]` (opcional): Fator de resolução (padrão: `480` -> $7680 \times 4320$).

Exemplo:
```bash
./bin/sequencial image_seq.ppm 480
```

