#!/bin/bash
# Script de medição de tempo e speedup FORA ou DENTRO do container
# Gera saída tabular e arquivo CSV em testes/resultados/benchmarks.csv

OUTPUT_DIR="testes/resultados"
mkdir -p "$OUTPUT_DIR"
CSV_FILE="$OUTPUT_DIR/benchmarks.csv"

# Localiza os binários
BIN_DIR="./bin"
if [ ! -d "$BIN_DIR" ] && [ -d "/app/bin" ]; then
    BIN_DIR="/app/bin"
fi

SEQ_BIN="$BIN_DIR/sequencial"
PROC_BIN="$BIN_DIR/processos"
THR_BIN="$BIN_DIR/threads"

FACTOR=480
REPETICOES=3

echo "=========================================================="
echo "    BENCHMARK MANDELBROT - PROCESSOS, THREADS E SEQUENCIAL"
echo "=========================================================="
echo "Fator de escala: $FACTOR (Resolução: $((16 * FACTOR))x$((9 * FACTOR)))"
echo "Repetições por teste: $REPETICOES"
echo "Arquivo de saída: $CSV_FILE"
echo "=========================================================="

# Inicializa cabeçalho do CSV
echo "Versao,Trabalhadores,CompTime_Segundos,IOTime_Segundos,TotalTime_Segundos,Speedup_Comp" > "$CSV_FILE"

# Função para extrair tempo computacional de saída
run_and_measure() {
    local cmd="$1"
    local total_comp=0

    for i in $(seq 1 $REPETICOES); do
        output=$($cmd)
        # Extrai o tempo de cálculo da linha "Tempo de Cálculo (Computacional): X.XXXXXX s"
        comp=$(echo "$output" | grep "Tempo de Cálculo" | awk '{print $4}')
        total_comp=$(awk -v t1="$total_comp" -v t2="$comp" 'BEGIN {print t1 + t2}')
    done

    # Média
    avg_comp=$(awk -v total="$total_comp" -v rep="$REPETICOES" 'BEGIN {printf "%.6f", total / rep}')
    echo "$avg_comp"
}

# 1. Medir Versão Sequencial
echo -n "Executando Sequencial... "
t_seq=$(run_and_measure "$SEQ_BIN image_seq.ppm $FACTOR")
echo "Média de cálculo: ${t_seq}s"
echo "Sequencial,1,$t_seq,0.0,$t_seq,1.00" >> "$CSV_FILE"

# 2. Medir Versão Processos (2, 4, 8)
for np in 2 4 8; do
    echo -n "Executando Processos ($np workers)... "
    t_proc=$(run_and_measure "$PROC_BIN $np image_proc_$np.ppm $FACTOR")
    speedup=$(awk -v seq="$t_seq" -v par="$t_proc" 'BEGIN {printf "%.2f", seq / par}')
    echo "Média de cálculo: ${t_proc}s (Speedup: ${speedup}x)"
    echo "Processos,$np,$t_proc,0.0,$t_proc,$speedup" >> "$CSV_FILE"
done

# 3. Medir Versão Threads (2, 4, 8)
for nt in 2 4 8; do
    echo -n "Executando Threads ($nt workers)... "
    t_thr=$(run_and_measure "$THR_BIN $nt image_thr_$nt.ppm $FACTOR")
    speedup=$(awk -v seq="$t_seq" -v par="$t_thr" 'BEGIN {printf "%.2f", seq / par}')
    echo "Média de cálculo: ${t_thr}s (Speedup: ${speedup}x)"
    echo "Threads,$nt,$t_thr,0.0,$t_thr,$speedup" >> "$CSV_FILE"
done

echo "=========================================================="
echo "Resultados salvos com sucesso em: $CSV_FILE"
echo "=========================================================="
cat "$CSV_FILE"

