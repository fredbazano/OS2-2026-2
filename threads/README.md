# Versão com Threads

Várias threads POSIX (`pthreads`) calculam a imagem juntas, no mesmo framebuffer. Um mutex (`pthread_mutex_t`) protege a fila de trabalho.

## Estratégia de paralelização

1. **Criação das threads:** a thread principal recebe a quantidade de threads pela linha de comando, cria as threads com `pthread_create()` e espera todas com `pthread_join()`. Depois, ela grava a imagem.

2. **Memória compartilhada:** as threads pertencem ao mesmo processo e compartilham o espaço de endereçamento. O framebuffer (alocado com `malloc`) e a fila de trabalho (`WorkQueue`) são vistos por todas, sem nenhum mecanismo extra.

3. **Divisão dinâmica do trabalho (fila de linhas):**
   - Os pixels são independentes, mas o custo varia muito: pontos dentro do conjunto vão até o limite de `MAX_ITERATIONS` iterações, enquanto pontos externos escapam em poucas. Por isso, algumas linhas custam muito mais que outras.
   - A fila é o contador compartilhado `next_row`: ao terminar uma linha, a thread pega a próxima linha livre. Quem pega linhas leves processa mais linhas, e todas terminam quase juntas.
   - Cada linha é calculada por uma única thread, então escrever os pixels não precisa de lock.

4. **Região crítica:** ler e incrementar `next_row`. Sem proteção, duas threads poderiam pegar a mesma linha ou pular uma. O mutex garante a exclusão mútua: `pthread_mutex_lock()`, pegar a linha e `pthread_mutex_unlock()`.

## Compilação
A partir da raiz do projeto:
```bash
make bin/threads
```
Ou manualmente:
```bash
gcc -O3 -Wall -Icomum threads/threads.c comum/mandelbrot.c -o bin/threads -lm -pthread
```

## Execução
```bash
./bin/threads <num_threads> [arquivo_saida] [factor]
./bin/threads 4 out/threads.ppm 480
```
- `<num_threads>`: quantidade de threads, obrigatória (ex.: 2, 4, 8).
- `[arquivo_saida]`: arquivo PPM gerado (padrão: `image.ppm`).
- `[factor]`: resolução `16*factor x 9*factor` (padrão: `480`, ou seja, 7680x4320).
