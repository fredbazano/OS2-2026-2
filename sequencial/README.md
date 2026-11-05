# Versão Sequencial

Um único fluxo de execução calcula as linhas da imagem uma a uma, de cima para baixo. É a referência para o speedup e para a imagem das versões paralelas.

## Código-fonte
- `sequencial.c`: aloca o framebuffer, calcula todas as linhas, grava o PPM e mede o tempo de cálculo e o de I/O.
- O cálculo de cada pixel, a gravação do PPM e a medição de tempo ficam em `comum/mandelbrot.c`, que é usado pelas três versões. Por isso todas produzem a mesma imagem.

## Compilação
A partir da raiz do projeto:
```bash
make bin/sequencial
```
Ou manualmente:
```bash
gcc -O3 -Wall -Icomum sequencial/sequencial.c comum/mandelbrot.c -o bin/sequencial -lm
```

## Execução
```bash
./bin/sequencial [arquivo_saida] [factor]
./bin/sequencial out/sequencial.ppm 480
```
- `[arquivo_saida]`: arquivo PPM gerado (padrão: `image.ppm`).
- `[factor]`: resolução `16*factor x 9*factor` (padrão: `480`, ou seja, 7680x4320).
