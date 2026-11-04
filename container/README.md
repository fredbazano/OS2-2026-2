# Mandelbrot - Ambiente em Container (Docker)

Esta pasta contém as configurações para execução isolada e portabilidade da aplicação através de containers Docker.

## Conteúdo
- `Dockerfile`: Imagem baseada em Ubuntu 24.04 contendo GCC, Make, dependências e compilando as três versões do projeto.
- `entrypoint.sh`: Script de entrada flexível para alternar facilmente entre `sequencial`, `processos`, `threads` ou benchmarks.

## Como Construir a Imagem Docker
A partir da raiz do projeto:
```bash
docker build -t mandelbrot -f container/Dockerfile .
```
Ou simplesmente:
```bash
docker build -t mandelbrot .
```

## Execução com Docker

### 1. Versão Sequencial
```bash
docker run --rm -v $(pwd)/out:/out mandelbrot sequencial image_seq.ppm 120
```

### 2. Versão com Processos
```bash
docker run --rm -v $(pwd)/out:/out mandelbrot processos 4 image_proc.ppm 120
```

### 3. Versão com Threads
```bash
docker run --rm -v $(pwd)/out:/out mandelbrot threads 4 image_thr.ppm 120
```

## Execução com Limitação de CPU (Requisito do Trabalho)
Conforme especificado no enunciado, as versões paralelas devem ser comparadas limitando o uso de CPUs pelo Docker:

```bash
# Limite de 1 CPU
docker run --rm --cpus="1" -v $(pwd)/out:/out mandelbrot processos 4 img_proc_cpu1.ppm 120

# Limite de 2 CPUs
docker run --rm --cpus="2" -v $(pwd)/out:/out mandelbrot processos 4 img_proc_cpu2.ppm 120

# Limite de 4 CPUs
docker run --rm --cpus="4" -v $(pwd)/out:/out mandelbrot processos 4 img_proc_cpu4.ppm 120
```

## Execução via Docker Compose
Caso prefira utilizar `docker-compose`:
```bash
# Executa sequencial
docker compose run --rm sequencial

# Executa processos com 2 CPUs
docker compose run --rm processos-cpu2

# Executa processos com 4 CPUs
docker compose run --rm processos-cpu4
```

