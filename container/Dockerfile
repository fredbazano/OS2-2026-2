# Imagem com as três versões do Mandelbrot já compiladas.
# Construir a partir da RAIZ do projeto:
#   docker build -t mandelbrot -f container/Dockerfile .
FROM ubuntu:24.04

# Dependências: compilador C e make (pacote build-essential)
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential \
 && rm -rf /var/lib/apt/lists/*

# Código da aplicação
WORKDIR /app
COPY Makefile    ./
COPY comum/      comum/
COPY sequencial/ sequencial/
COPY processos/  processos/
COPY threads/    threads/

# Compila em /app/bin e deixa os programas acessíveis pelo nome
RUN make
ENV PATH="/app/bin:${PATH}"

# Pasta onde as imagens são gravadas (use -v "$(pwd)/out:/out" para recebê-las no host)
WORKDIR /out
