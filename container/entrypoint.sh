#!/bin/bash
set -e

# entrypoint.sh - Script de inicialização do container Mandelbrot

case "$1" in
    sequencial)
        shift
        # Se nenhum argumento for passado, usa valores padrão
        if [ $# -eq 0 ]; then
            exec /app/bin/sequencial "image_seq.ppm" 480
        else
            exec /app/bin/sequencial "$@"
        fi
        ;;
    processos)
        shift
        # Se não especificou número de processos, usa 4 por padrão
        if [ $# -eq 0 ]; then
            exec /app/bin/processos 4 "image_proc.ppm" 480
        else
            exec /app/bin/processos "$@"
        fi
        ;;
    threads)
        shift
        # Se não especificou número de threads, usa 4 por padrão
        if [ $# -eq 0 ]; then
            exec /app/bin/threads 4 "image_threads.ppm" 480
        else
            exec /app/bin/threads "$@"
        fi
        ;;
    testes|benchmark)
        shift
        if [ -f /app/testes/executar_testes.sh ]; then
            exec /app/testes/executar_testes.sh "$@"
        else
            echo "Script de testes não encontrado."
            exit 1
        fi
        ;;
    help|--help|-h)
        echo "=========================================================="
        echo "               Mandelbrot PPM Container                   "
        echo "=========================================================="
        echo "Uso:"
        echo "  docker run --rm mandelbrot sequencial [arquivo_saida] [factor]"
        echo "  docker run --rm mandelbrot processos <num_processos> [arquivo_saida] [factor]"
        echo "  docker run --rm mandelbrot threads <num_threads> [arquivo_saida] [factor]"
        echo "  docker run --rm mandelbrot testes"
        echo ""
        echo "Exemplo com volume e limite de CPU:"
        echo "  docker run --rm --cpus=\"2\" -v \$(pwd)/out:/out mandelbrot processos 4 image_proc.ppm 120"
        echo "=========================================================="
        exit 0
        ;;
    *)
        # Executa qualquer outro comando passado (ex: bash, sh, ls, etc.)
        exec "$@"
        ;;
esac

