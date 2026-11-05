#!/bin/bash
# Benchmark DENTRO do container com limite de CPU (Gráfico 3).
# Em containers limitados a 1, 2 e 4 CPUs (docker run --cpus), executa a versão
# sequencial e as paralelas com 2, 4 e 8 trabalhadores (média de REPETICOES execuções).
# O sequencial de cada limite é a referência para o speedup e para a imagem:
# o hash (md5) de cada imagem é calculado dentro do container e comparado com o dele.
# Para comparar com os tempos FORA do container (testes/resultados/benchmarks.csv).
# Saída: testes/resultados/docker_benchmarks.csv
#
# Uso: ./testes/executar_testes_docker.sh
#      FACTOR=60 REPETICOES=1 ./testes/executar_testes_docker.sh   (teste rápido)

set -eo pipefail
cd "$(dirname "$0")/.."   # roda a partir da raiz do projeto

FACTOR=${FACTOR:-480}         # mesma entrada do benchmark fora do container
REPETICOES=${REPETICOES:-3}
TRABALHADORES="2 4 8"
LIMITES_CPU="1 2 4"
IMAGEM="mandelbrot"
CSV="testes/resultados/docker_benchmarks.csv"

# Roda a versão no container REPETICOES vezes e imprime: "calculo io total md5"
# (médias dos tempos; md5 da imagem gerada na última execução)
# Uso: medir <cpus> <comando do programa...>
medir() {
    local cpus=$1; shift
    for i in $(seq "$REPETICOES"); do
        # A imagem é gravada dentro do container e descartada com ele (--rm)
        docker run --rm --cpus="$cpus" "$IMAGEM" \
            sh -c "$* /tmp/imagem.ppm $FACTOR && md5sum /tmp/imagem.ppm" |
        awk -F: '/Tempo de Cálculo/ {c=$2} /Tempo de Gravação/ {io=$2} /Tempo Total/ {t=$2}
                 /imagem.ppm$/ {split($0, m, " "); h=m[1]}
                 END {print c+0, io+0, t+0, h}'
    done | awk '{c+=$1; io+=$2; t+=$3; h=$4} END {printf "%.6f %.6f %.6f %s\n", c/NR, io/NR, t/NR, h}'
}

# (Re)constrói a imagem para garantir que o container usa o código atual
echo "Construindo a imagem Docker '$IMAGEM'..."
docker build -q -t "$IMAGEM" -f container/Dockerfile . > /dev/null
mkdir -p "$(dirname "$CSV")"

echo "=========================================================="
echo "  BENCHMARK DENTRO DO CONTAINER - $((16 * FACTOR))x$((9 * FACTOR)), $REPETICOES repetições"
echo "=========================================================="

echo "Versao,CPUs,Trabalhadores,Calculo_s,IO_s,Total_s,Speedup_Calculo,Speedup_Total,Imagem_Igual_Sequencial" > "$CSV"

for cpus in $LIMITES_CPU; do
    echo "--- Limite de $cpus CPU(s) ---"

    # 1. Sequencial (referência deste limite de CPU)
    echo -n "Sequencial... "
    read -r seq_calc seq_io seq_total seq_md5 <<< "$(medir "$cpus" sequencial)"
    echo "cálculo ${seq_calc}s | total ${seq_total}s"
    echo "Sequencial,$cpus,1,$seq_calc,$seq_io,$seq_total,1.00,1.00,sim" >> "$CSV"

    # 2. Processos e threads com 2, 4 e 8 trabalhadores
    for versao in processos threads; do
        for n in $TRABALHADORES; do
            echo -n "$versao ($n)... "
            read -r calc io total md5 <<< "$(medir "$cpus" "$versao" "$n")"

            sp_calc=$(awk -v s="$seq_calc" -v p="$calc" 'BEGIN {printf "%.2f", s / p}')
            sp_total=$(awk -v s="$seq_total" -v p="$total" 'BEGIN {printf "%.2f", s / p}')
            if [ "$md5" = "$seq_md5" ]; then igual=sim; else igual=NAO; fi

            echo "cálculo ${calc}s | total ${total}s | speedup ${sp_total}x | imagem igual: $igual"
            echo "$versao,$cpus,$n,$calc,$io,$total,$sp_calc,$sp_total,$igual" >> "$CSV"
        done
    done
done

echo "=========================================================="
echo "Resultados salvos em: $CSV"
echo "=========================================================="
column -s, -t < "$CSV"
