# Mandelbrot PPM — Programação Paralela

Gera o fractal de Mandelbrot como imagem PPM (P6) e compara três implementações:

1. **Sequencial**
2. **Processos** com memória compartilhada (`fork` + `mmap` + semáforo `sem_t`)
3. **Threads** (`pthreads` + `mutex`)

As versões paralelas dividem o trabalho com uma **fila dinâmica de linhas**: cada trabalhador pega a próxima linha livre ao terminar a anterior. A estratégia de cada versão está explicada no README da sua pasta.

## Estrutura

| Pasta | Conteúdo |
|---|---|
| `sequencial/`, `processos/`, `threads/` | Código-fonte e README de cada versão |
| `comum/` | Código igual nas três versões: cálculo do pixel, gravação do PPM e medição de tempo |
| `container/` | `Dockerfile` e instruções de execução em container |
| `testes/` | Scripts de benchmark, `entradas/` (entrada usada) e `resultados/` (CSVs) |
| `documentacao/` | Apresentação |

---

## 1. Instalar dependências

Linux / WSL (Ubuntu, Debian):
```bash
sudo apt-get update
sudo apt-get install -y build-essential
```

Para executar com Docker, basta ter o Docker instalado e em execução (seção 6).

## 2. Compilar

```bash
make
```

Gera `bin/sequencial`, `bin/processos` e `bin/threads` e cria a pasta `out/` para as imagens. `make clean` apaga os executáveis e as imagens.

## 3. Executar a versão sequencial

```bash
./bin/sequencial [arquivo_saida] [factor]
./bin/sequencial out/sequencial.ppm 480
```

## 4. Executar a versão com processos

```bash
./bin/processos <num_processos> [arquivo_saida] [factor]
./bin/processos 4 out/processos.ppm 480
```

## 5. Executar a versão com threads

```bash
./bin/threads <num_threads> [arquivo_saida] [factor]
./bin/threads 4 out/threads.ppm 480
```

**Parâmetros (iguais nas três versões):**
- `<num_processos>` / `<num_threads>`: quantidade de trabalhadores, obrigatória (ex.: 2, 4, 8). Não é fixa no código.
- `[arquivo_saida]`: arquivo PPM gerado (padrão: `image.ppm`).
- `[factor]`: resolução `16*factor x 9*factor` (padrão: `480`, ou seja, 7680x4320).

Cada execução mostra o tempo de cálculo, o tempo de gravação (I/O) e o tempo total do programa (do início ao fim do `main`).

## 6. Executar com Docker

```bash
# Construir a imagem (a partir da raiz do projeto)
docker build -t mandelbrot -f container/Dockerfile .

# Executar: mesmos argumentos de fora do container; -v recebe a imagem em out/
docker run --rm -v "$(pwd)/out:/out" mandelbrot threads 4 threads.ppm 480

# Limitar a CPU (1, 2 ou 4)
docker run --rm --cpus="2" mandelbrot processos 4 processos.ppm 480
```

Mais detalhes em [`container/README.md`](container/README.md).

## 7. Experimentos

```bash
./testes/executar_testes.sh          # fora do container (Gráficos 1 e 2)
./testes/executar_testes_docker.sh   # dentro do container, 1/2/4 CPUs (Gráfico 3)
```

- **`executar_testes.sh`:** compila e roda o sequencial e as versões com 2, 4 e 8 processos/threads (média de 5 execuções). Calcula o speedup e confere se cada imagem é idêntica à do sequencial. Saída: `testes/resultados/benchmarks.csv`.
- **`executar_testes_docker.sh`:** reconstrói a imagem Docker e faz o mesmo em containers limitados a 1, 2 e 4 CPUs. O speedup e a imagem são comparados com o sequencial do mesmo limite. Saída: `testes/resultados/docker_benchmarks.csv`.

Os resultados usados nos gráficos e na apresentação estão congelados em `testes/resultados/final_*.csv` (ver [`testes/resultados/README.md`](testes/resultados/README.md)). A entrada usada está descrita em [`testes/entradas/`](testes/entradas/README.md). Os scripts podem ser chamados de qualquer pasta. Para um teste rápido, com imagem pequena e uma repetição:
```bash
FACTOR=60 REPETICOES=1 ./testes/executar_testes.sh
```
