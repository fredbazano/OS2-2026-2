# Mandelbrot - Versão Paralela com Múltiplos Processos e Memória Compartilhada

Esta pasta contém a implementação paralela em C utilizando múltiplos processos independentes (`fork()`), memória compartilhada (`mmap`) e semáforos POSIX (`sem_t`) para sincronização em região crítica.

## Estratégia de Paralelização e Conceitos do SO

1. **Criação de Processos (`fork`)**:
   - O processo pai recebe o número de trabalhadores (`num_processes`) via linha de comando e cria $N$ processos filhos usando `fork()`.
   - O pai aguarda a finalização de todos os filhos com chamadas a `waitpid()`.

2. **Memória Compartilhada (`mmap` com `MAP_SHARED`)**:
   - Para permitir que todos os processos escrevam diretamente na mesma matriz de imagem sem necessidade de IPC por pipes/sockets, o framebuffer é alocado através de `mmap(NULL, size, PROT_READ | PROT_WRITE, MAP_SHARED | MAP_ANONYMOUS, -1, 0)`.
   - A mesma abordagem de memória compartilhada é utilizada para a estrutura `SharedState` que consolida as métricas globais de processamento.

3. **Divisão de Trabalho (Balanceamento de Carga)**:
   - Utiliza-se a estratégia de **linhas intercaladas (Round-Robin / Cyclic)**: o processo filho com índice $p$ calcula todas as linhas $y$ em que `y % num_processes == p`.
   - Essa abordagem evita o problema clássico de desbalanceamento no conjunto de Mandelbrot: a região central (que exige o número máximo de 1500 iterações) e as regiões externas (que escapam rapidamente em 1 a 10 iterações) são distribuídas uniformemente entre todos os processos.

4. **Sincronização e Região Crítica (`sem_t`)**:
   - Um semáforo compartilhado entre processos (`sem_init(&shared->sem_lock, 1, 1)`) protege a atualização das variáveis globais (`total_iterations` e `workers_completed`).
   - Cada processo filho realiza `sem_wait()` antes de atualizar o estado global e `sem_post()` ao sair da região crítica.

## Compilação
A partir da raiz do projeto:
```bash
make bin/processos
```
Ou manualmente com `gcc`:
```bash
gcc -O3 -Wall processos/processes-ppm.c -o bin/processos -lm -pthread
```

## Execução
```bash
./bin/processos <num_processos> [arquivo_saida] [factor]
```
Parâmetros:
- `<num_processos>` (obrigatório): Quantidade de processos a serem criados (ex: `2`, `4`, `8`).
- `[arquivo_saida]` (opcional): Nome do arquivo `.ppm` gerado (padrão: `image.ppm`).
- `[factor]` (opcional): Fator de resolução (padrão: `480` -> $7680 \times 4320$).

Exemplos:
```bash
# Executando com 2 processos
./bin/processos 2 image_proc_2.ppm 480

# Executando com 4 processos
./bin/processos 4 image_proc_4.ppm 480

# Executando com 8 processos
./bin/processos 8 image_proc_8.ppm 480
```

