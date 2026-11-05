# Resultados dos experimentos

## Resultados finais (usados nos gráficos e na apresentação)

| Arquivo | Origem | Gráficos |
|---|---|---|
| `final_fora_container.csv` | `testes/executar_testes.sh` | 1 (tempo) e 2 (speedup) |
| `final_dentro_container.csv` | `testes/executar_testes_docker.sh` | 3 (fora x dentro do container) |

Esses dois arquivos são cópias congeladas de uma execução e **não são sobrescritos** pelos scripts. Novas execuções gravam em `benchmarks.csv` e `docker_benchmarks.csv`.

**Condições da execução final:**
- **Data:** 05/11/2026.
- **Entrada:** `factor=480` (7680x4320); média de 3 execuções por configuração. Detalhes em [`../entradas/`](../entradas/README.md).
- **Máquina:** Intel Core i5-12600K, WSL2 (Ubuntu 22.04) com 8 CPUs lógicas visíveis (4 núcleos x 2 threads); gcc 11.4 com `-O3`.
- **Container:** Docker 29.9.2 (Docker Desktop), imagem de `container/Dockerfile`.

## Colunas

- `Calculo_s`, `IO_s`, `Total_s`: tempo de cálculo, de gravação da imagem e total, em segundos (média).
- `Speedup_Calculo`, `Speedup_Total`: tempo do sequencial dividido pelo tempo da versão. Dentro do container, a referência é o sequencial **com o mesmo limite de CPU**.
- `Imagem_Igual_Sequencial`: `sim` se a imagem gerada é idêntica, byte a byte, à do sequencial (`cmp` fora do container, `md5sum` dentro).
- `CPUs` (só dentro do container): limite aplicado com `docker run --cpus`.
