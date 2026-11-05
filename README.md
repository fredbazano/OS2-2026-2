# Trabalho Prático — Programação Paralela e Concorrência

Projeto de computação paralela comparando três implementações de renderização do fractal de **Mandelbrot** em formato PPM (P6):
1. **Versão Sequencial**
2. **Versão Paralela com Múltiplos Processos e Memória Compartilhada (`mmap` + `sem_t`)**
3. **Versão Paralela com Múltiplas Threads (`pthreads` + `mutex`)**
4. **Execução em Containers Docker com limites de CPU (`--cpus="1"`, `2`, `4`)**

---

## 1. Instalação de Dependências

### No Linux / Ubuntu / Debian / WSL:
```bash
sudo apt-get update
sudo apt-get install -y build-essential make gcc
```

### Com Docker (dispensa dependências locais no sistema operacional):
Apenas garanta que o [Docker Desktop / Docker Engine](https://docs.docker.com/get-docker/) esteja em execução na máquina.

---

## 2. Como Compilar o Programa

Para compilar todas as versões simultaneamente:
```bash
make
```
Os executáveis gerados estarão localizados em `bin/`:
- `bin/sequencial`
- `bin/processos`
- `bin/threads`

Para limpar os arquivos compilados e imagens geradas:
```bash
make clean
```

---

## 3. Como Executar a Versão Sequencial

```bash
./bin/sequencial [arquivo_saida] [factor]
```
- `arquivo_saida` (opcional, padrão `image.ppm`)
- `factor` (opcional, padrão `480` correspondendo à resolução 8K $7680 \times 4320$).

Exemplo:
```bash
./bin/sequencial out/image_seq.ppm 480
```

---

## 4. Como Executar a Versão com Processos

O número de processos **não é fixo no código** e é fornecido como primeiro argumento:

```bash
./bin/processos <num_processos> [arquivo_saida] [factor]
```

Exemplos recomendados para análise experimental (2, 4 e 8 processos):
```bash
# Execução com 2 processos
./bin/processos 2 out/image_proc_2.ppm 480

# Execução com 4 processos
./bin/processos 4 out/image_proc_4.ppm 480

# Execução com 8 processos
./bin/processos 8 out/image_proc_8.ppm 480
```

> **Destaques da Implementação de Processos:**
> - Utilização de **Memória Compartilhada** POSIX (`mmap` com flag `MAP_SHARED | MAP_ANONYMOUS`) para o framebuffer e estatísticas.
> - **Divisão de Trabalho Intercalada** (linhas em round-robin: linha $y$ no processo $p$ se `y % num_processes == p`), eliminando gargalos de balanceamento de carga no Mandelbrot.
> - **Região Crítica** controlada por semáforo POSIX compartilhado (`sem_t` inicializado com `pshared=1`).

---

## 5. Como Executar a Versão com Threads

```bash
./bin/threads <num_threads> [arquivo_saida] [factor]
```

Exemplos recomendados para análise experimental (2, 4 e 8 threads):
```bash
# Execução com 2 threads
./bin/threads 2 out/image_thr_2.ppm 480

# Execução com 4 threads
./bin/threads 4 out/image_thr_4.ppm 480

# Execução com 8 threads
./bin/threads 8 out/image_thr_8.ppm 480
```

---

## 6. Execução com Docker (Container)

### Construção da Imagem:
```bash
docker build -t mandelbrot .
```

### Execução Simples:
```bash
# Sequencial
docker run --rm -v $(pwd)/out:/out mandelbrot sequencial

# Processos (ex: 4 processos)
docker run --rm -v $(pwd)/out:/out mandelbrot processos 4

# Threads (ex: 4 threads)
docker run --rm -v $(pwd)/out:/out mandelbrot threads 4
```

### Execução com Limitação de CPU:
Para avaliar o comportamento com restrições de hardware, execute limitando a quantidade de CPUs:
```bash
# Limite de 1 CPU
docker run --rm --cpus="1" -v $(pwd)/out:/out mandelbrot processos 4 img_p4_cpu1.ppm 480

# Limite de 2 CPUs
docker run --rm --cpus="2" -v $(pwd)/out:/out mandelbrot processos 4 img_p4_cpu2.ppm 480

# Limite de 4 CPUs
docker run --rm --cpus="4" -v $(pwd)/out:/out mandelbrot processos 4 img_p4_cpu4.ppm 480
```

---

## 7. Automação dos Experimentos e Geração dos Gráficos

Para rodar automaticamente os benchmarks e gerar os arquivos CSV necessários para os **Gráficos 1, 2 e 3**:

```bash
# Execução Fora do Container (Gráficos 1 e 2):
./testes/executar_testes.sh

# Execução Dentro do Container com limites de 1, 2 e 4 CPUs (Gráfico 3):
./testes/executar_testes_docker.sh
```

Os resultados serão gravados em `testes/resultados/` prontos para serem importados no software de planilhas/gráficos.

