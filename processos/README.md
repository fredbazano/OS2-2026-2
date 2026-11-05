# Versão com Processos e Memória Compartilhada

Vários processos (`fork`) calculam a imagem juntos, escrevendo num framebuffer em memória compartilhada (`mmap`). Um semáforo (`sem_t`) protege a fila de trabalho.

## Estratégia de paralelização

1. **Criação dos processos:** o pai recebe a quantidade de processos pela linha de comando, cria os filhos com `fork()` e espera todos com `waitpid()`. Depois, o pai grava a imagem.

2. **Memória compartilhada:** o framebuffer e a estrutura `SharedState` (fila de trabalho e semáforo) são alocados com `mmap(..., MAP_SHARED | MAP_ANONYMOUS, ...)` **antes** do `fork()`, então os filhos herdam o mapeamento e escrevem direto na mesma imagem. Sem `MAP_SHARED`, cada filho escreveria numa cópia própria (copy-on-write) e o pai receberia a imagem vazia.

3. **Divisão dinâmica do trabalho (fila de linhas):**
   - Os pixels são independentes, mas o custo varia muito: pontos dentro do conjunto vão até o limite de `MAX_ITERATIONS` iterações, enquanto pontos externos escapam em poucas. Por isso, algumas linhas custam muito mais que outras.
   - A fila é o contador compartilhado `next_row`: ao terminar uma linha, o processo pega a próxima linha livre. Quem pega linhas leves processa mais linhas, e todos terminam quase juntos.
   - Cada linha é calculada por um único processo, então escrever os pixels não precisa de lock.

4. **Região crítica:** ler e incrementar `next_row`. Sem proteção, dois processos poderiam pegar a mesma linha ou pular uma. Um semáforo binário compartilhado entre processos garante a exclusão mútua: `sem_init(&shared->sem_lock, 1, 1)`, em que `pshared=1` e o valor inicial é 1. A sequência é `sem_wait()`, pegar a linha e `sem_post()`.

## Compilação
A partir da raiz do projeto:
```bash
make bin/processos
```
Ou manualmente:
```bash
gcc -O3 -Wall -Icomum processos/processos.c comum/mandelbrot.c -o bin/processos -lm -pthread
```

## Execução
```bash
./bin/processos <num_processos> [arquivo_saida] [factor]
./bin/processos 4 out/processos.ppm 480
```
- `<num_processos>`: quantidade de processos, obrigatória (ex.: 2, 4, 8).
- `[arquivo_saida]`: arquivo PPM gerado (padrão: `image.ppm`).
- `[factor]`: resolução `16*factor x 9*factor` (padrão: `480`, ou seja, 7680x4320).
