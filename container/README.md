# Execução em Container (Docker)

O `Dockerfile` desta pasta cria uma imagem Ubuntu 24.04 com o compilador C (`build-essential`) e as três versões já compiladas. Basta ter o Docker instalado e em execução: nada é instalado no sistema do usuário.

## Construir a imagem
A partir da **raiz** do projeto, porque o código-fonte fica fora desta pasta:
```bash
docker build -t mandelbrot -f container/Dockerfile .
```

## Executar
Os programas são chamados pelo nome, com os mesmos argumentos de fora do container. O `-v` monta a pasta `out/` do projeto para receber a imagem gerada.
```bash
docker run --rm -v "$(pwd)/out:/out" mandelbrot sequencial sequencial.ppm 480
docker run --rm -v "$(pwd)/out:/out" mandelbrot processos 4 processos.ppm 480
docker run --rm -v "$(pwd)/out:/out" mandelbrot threads 4 threads.ppm 480
```

## Executar com limite de CPU
`--cpus` limita o tempo de CPU que o container pode usar:
```bash
docker run --rm --cpus="1" mandelbrot processos 4 processos.ppm 480
docker run --rm --cpus="2" mandelbrot processos 4 processos.ppm 480
docker run --rm --cpus="4" mandelbrot processos 4 processos.ppm 480
```
Sem o `-v`, a imagem fica dentro do container e é descartada com ele (`--rm`). Isso basta quando o objetivo é só medir o tempo.

## Benchmark
`testes/executar_testes_docker.sh` reconstrói a imagem e roda o sequencial e as versões com 2, 4 e 8 processos/threads em containers limitados a 1, 2 e 4 CPUs.
