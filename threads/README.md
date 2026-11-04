# Mandelbrot - Versão Paralela com Múltiplas Threads (POSIX Threads)

Esta pasta contém a implementação paralela em C utilizando múltiplas threads (`pthread_create`), espaço de memória compartilhado nativo e exclusão mútua (`pthread_mutex_t`).

## Estratégia de Paralelização e Conceitos do SO

1. **Criação e Gestão de Threads (`pthreads`)**:
   - A thread principal (main) recebe a quantidade de threads desejada via linha de comando (`num_threads`).
   - Dispara $N$ threads com `pthread_create()` e aguarda a conclusão de todas com `pthread_join()`.

2. **Memória Compartilhada**:
   - Como todas as threads pertencem ao mesmo processo, elas compartilham diretamente o espaço de endereçamento do heap onde o framebuffer da imagem reside.

3. **Divisão de Trabalho**:
   - Aplica-se a divisão por linhas intercaladas: a thread $t$ processa as linhas `y % num_threads == t`.

4. **Região Crítica e Exclusão Mútua (`pthread_mutex_t`)**:
   - A acumulação do total de iterações calculadas é protegida por um mutex (`pthread_mutex_lock` / `pthread_mutex_unlock`) para evitar condições de corrida (race conditions).

## Compilação
A partir da raiz do projeto:
```bash
make bin/threads
```
Ou manualmente:
```bash
gcc -O3 -Wall threads/threads-ppm.c -o bin/threads -lm -pthread
```

## Execução
```bash
./bin/processos <num_threads> [arquivo_saida] [factor]
```
Parâmetros:
- `<num_threads>` (obrigatório): Quantidade de threads a serem criadas (ex: `2`, `4`, `8`).
- `[arquivo_saida]` (opcional): Nome do arquivo `.ppm` gerado (padrão: `image.ppm`).
- `[factor]` (opcional): Fator de resolução (padrão: `480` -> $7680 \times 4320$).

Exemplos:
```bash
./bin/threads 2 image_thr_2.ppm 480
./bin/threads 4 image_thr_4.ppm 480
./bin/threads 8 image_thr_8.ppm 480
```

