# Entrada de teste

A aplicação não lê arquivo de entrada. A entrada são os parâmetros da linha de comando:

| Parâmetro | Valores nos testes | Significado |
|---|---|---|
| `factor` | `480` | Resolução `16*factor x 9*factor` = **7680x4320** (8K, cerca de 33 milhões de pixels) |
| Processos/threads | `2`, `4` e `8` | Quantidade de trabalhadores das versões paralelas |
| Limite de CPU (Docker) | `1`, `2` e `4` | `docker run --cpus=...` |

Fixos no código (`comum/`): até `MAX_ITERATIONS` iterações por pixel e raio de escape 2.

Com essa entrada, a versão sequencial leva bem mais que os 2 segundos mínimos pedidos no trabalho.

```bash
./bin/sequencial out/sequencial.ppm 480
./bin/processos 4 out/processos.ppm 480
./bin/threads 4 out/threads.ppm 480
```

Os dois scripts de `testes/` usam essa mesma entrada.
