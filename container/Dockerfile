# Multi-stage build ou imagem limpa para compilação e execução
FROM ubuntu:24.04

# Evita prompts interativos durante a instalação
ENV DEBIAN_FRONTEND=noninteractive

# Instalação do compilador GCC, Make e utilitários
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    make \
    gcc \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Diretório base da aplicação
WORKDIR /app

# Copia arquivos do projeto
COPY Makefile ./
COPY sequencial/ sequencial/
COPY processos/  processos/
COPY threads/    threads/
COPY testes/     testes/

# Compila as versões sequencial, processos e threads
RUN make all

# Copia e configura o script de inicialização
COPY container/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh \
 && chmod +x /app/testes/*.sh 2>/dev/null || true

# Disponibiliza os executáveis globalmente no PATH
ENV PATH="/app/bin:${PATH}"

# Cria e define o diretório de trabalho padrão para saída de imagens
WORKDIR /out
VOLUME ["/out"]

ENTRYPOINT ["entrypoint.sh"]
CMD ["processos", "4", "image_proc.ppm", "480"]

