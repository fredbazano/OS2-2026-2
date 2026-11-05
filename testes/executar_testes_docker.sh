#!/bin/bash
# Executa os benchmarks em container com limites de 1, 2 e 4 CPUs
# Gera tabela comparativa em testes/resultados/docker_benchmarks.csv

OUTPUT_DIR="testes/resultados"
mkdir -p "$OUTPUT_DIR"
CSV_FILE="$OUTPUT_DIR/docker_benchmarks.csv"

echo "=========================================================="
echo "    BENCHMARK MANDELBROT DENTRO DO DOCKER (Limites de CPU)"
echo "=========================================================="
echo "Versao,CPULimit,Workers,CompTime_Segundos" > "$CSV_FILE"

IMAGE_NAME="mandelbrot"

for cpu_limit in 1 2 4; do
    echo "--- Testando com limite de $cpu_limit CPU(s) ---"
    
    # Processos: 2, 4, 8
    for np in 2 4 8; do
        echo -n "Docker (cpus=$cpu_limit) - Processos ($np)... "
        output=$(docker run --rm --cpus="$cpu_limit" "$IMAGE_NAME" processos "$np" "img_p${np}_cpu${cpu_limit}.ppm" 480)
        comp=$(echo "$output" | grep "Tempo de Cálculo" | awk '{print $4}')
        echo "${comp}s"
        echo "Processos,$cpu_limit,$np,$comp" >> "$CSV_FILE"
    done

    # Threads: 2, 4, 8
    for nt in 2 4 8; do
        echo -n "Docker (cpus=$cpu_limit) - Threads ($nt)... "
        output=$(docker run --rm --cpus="$cpu_limit" "$IMAGE_NAME" threads "$nt" "img_t${nt}_cpu${cpu_limit}.ppm" 480)
        comp=$(echo "$output" | grep "Tempo de Cálculo" | awk '{print $4}')
        echo "${comp}s"
        echo "Threads,$cpu_limit,$nt,$comp" >> "$CSV_FILE"
    done
done

echo "=========================================================="
echo "Benchmark Docker concluído! Dados gravados em $CSV_FILE"
echo "=========================================================="
cat "$CSV_FILE"

