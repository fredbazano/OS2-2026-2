#!/bin/bash
# Benchmark FORA do container (Gráficos 1 e 2).
# Mede a versão sequencial e as paralelas com 2, 4 e 8 trabalhadores,
# tira a média de REPETICOES execuções, calcula o speedup e confere se
# cada versão paralela gera exatamente a mesma imagem da sequencial.
# Saída: testes/resultados/benchmarks.csv
#
# Uso: ./testes/executar_testes.sh
#      FACTOR=60 REPETICOES=1 ./testes/executar_testes.sh   (teste rápido)

set -eo pipefail
cd "$(dirname "$0")/.."   # roda a partir da raiz do projeto

FACTOR=${FACTOR:-480}         # 480 -> 7680x4320 (ver testes/entradas)
REPETICOES=${REPETICOES:-5}
TRABALHADORES="2 4 8"
OUT_DIR="out"                 # imagens geradas (apagadas pelo make clean)
CSV="testes/resultados/benchmarks.csv"

# Executa o comando REPETICOES vezes e imprime as médias: "calculo io total"
medir() {
    for i in $(seq "$REPETICOES"); do
        "$@" | awk -F: '/Tempo de Cálculo/ {c=$2} /Tempo de Gravação/ {io=$2} /Tempo Total/ {t=$2}
                        END {print c+0, io+0, t+0}'
    done | awk '{c+=$1; io+=$2; t+=$3} END {printf "%.6f %.6f %.6f\n", c/NR, io/NR, t/NR}'
}

make -s all
mkdir -p "$OUT_DIR" "$(dirname "$CSV")"

echo "=========================================================="
echo "  BENCHMARK FORA DO CONTAINER - $((16 * FACTOR))x$((9 * FACTOR)), $REPETICOES repetições"
echo "=========================================================="

echo "Versao,Trabalhadores,Calculo_s,IO_s,Total_s,Speedup_Calculo,Speedup_Total,Imagem_Igual_Sequencial" > "$CSV"

# 1. Sequencial (referência para o speedup e para a imagem)
echo -n "Sequencial... "
read -r seq_calc seq_io seq_total <<< "$(medir ./bin/sequencial "$OUT_DIR/sequencial.ppm" "$FACTOR")"
echo "cálculo ${seq_calc}s | total ${seq_total}s"
echo "Sequencial,1,$seq_calc,$seq_io,$seq_total,1.00,1.00,sim" >> "$CSV"

# 2. Processos e threads com 2, 4 e 8 trabalhadores
for versao in processos threads; do
    for n in $TRABALHADORES; do
        echo -n "$versao ($n)... "
        read -r calc io total <<< "$(medir ./bin/$versao "$n" "$OUT_DIR/paralelo.ppm" "$FACTOR")"

        sp_calc=$(awk -v s="$seq_calc" -v p="$calc" 'BEGIN {printf "%.2f", s / p}')
        sp_total=$(awk -v s="$seq_total" -v p="$total" 'BEGIN {printf "%.2f", s / p}')

        # Requisito: as versões devem produzir resultados equivalentes
        if cmp -s "$OUT_DIR/sequencial.ppm" "$OUT_DIR/paralelo.ppm"; then igual=sim; else igual=NAO; fi

        echo "cálculo ${calc}s | total ${total}s | speedup ${sp_total}x | imagem igual: $igual"
        echo "$versao,$n,$calc,$io,$total,$sp_calc,$sp_total,$igual" >> "$CSV"
    done
done

rm -f "$OUT_DIR/sequencial.ppm" "$OUT_DIR/paralelo.ppm"

echo "=========================================================="
echo "Resultados salvos em: $CSV"
echo "=========================================================="
column -s, -t < "$CSV"
