# Fonte da apresentação

- `gerar_apresentacao.py`: lê `testes/resultados/final_*.csv`, desenha os gráficos (SVG) e gera `apresentacao.html` com os slides. Usa só a biblioteca padrão do Python.
- `mandelbrot.png`: imagem do fractal usada nos slides (`./bin/sequencial` com `factor=80`, 1280x720, o tamanho do slide).
- `graficos/`: os gráficos em SVG separados.

## Gerar
```bash
python3 documentacao/fonte/gerar_apresentacao.py
```
Para o PDF, abra `apresentacao.html` no Chrome/Edge e use **Imprimir → Salvar como PDF**, com margens "Nenhuma" e sem cabeçalhos/rodapés. As páginas já têm o tamanho de slide (1280x720).
