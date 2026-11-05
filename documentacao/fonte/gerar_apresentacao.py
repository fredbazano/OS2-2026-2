#!/usr/bin/env python3
"""Gera os slides da apresentação (HTML) com os gráficos a partir dos CSVs finais.

Uso (a partir da raiz do projeto):
    python3 documentacao/fonte/gerar_apresentacao.py

Saída: documentacao/fonte/apresentacao.html e documentacao/fonte/graficos/*.svg
O PDF é gerado imprimindo o HTML (ver documentacao/fonte/README.md).
Usa só a biblioteca padrão do Python.
"""
import base64
import csv
import html
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
FONTE = RAIZ / "documentacao" / "fonte"
FORA = RAIZ / "testes" / "resultados" / "final_fora_container.csv"
DENTRO = RAIZ / "testes" / "resultados" / "final_dentro_container.csv"

# Cores (paleta validada: azul/laranja são os dois primeiros slots categóricos)
COR = {
    "Sequencial": "#8b8a83",
    "processos": "#2a78d6",
    "threads": "#eb6834",
    "fora": "#52514e",
    "1": "#9ec5f4",   # rampa azul: limite de CPU maior = mais escuro
    "2": "#3987e5",
    "4": "#184f95",
}
TEXTO, TEXTO2, MUDO = "#0b0b0b", "#52514e", "#8b8a83"
GRADE, EIXO, FUNDO = "#e1e0d9", "#c3c2b7", "#fcfcfb"


def num(v, casas=2):
    return f"{v:.{casas}f}".replace(".", ",")


def ler_csv(caminho):
    with open(caminho, encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------- gráficos SVG

def ticks(maximo, n=5):
    """Valores 'redondos' para o eixo y, de 0 até cobrir maximo."""
    bruto = maximo / n
    for passo in (0.5, 1, 2, 2.5, 5, 10, 20):
        if passo >= bruto:
            break
    topo = passo * int(-(-maximo // passo))
    return [i * passo for i in range(int(topo / passo) + 1)], topo


def barra(x, y_topo, largura, y_base, cor, raio=4):
    """Barra com a ponta de dados arredondada e a base reta na linha zero."""
    r = min(raio, largura / 2, max(y_base - y_topo, 0))
    return (f'<path d="M{x:.1f},{y_base:.1f} V{y_topo + r:.1f} '
            f'Q{x:.1f},{y_topo:.1f} {x + r:.1f},{y_topo:.1f} H{x + largura - r:.1f} '
            f'Q{x + largura:.1f},{y_topo:.1f} {x + largura:.1f},{y_topo + r:.1f} '
            f'V{y_base:.1f} Z" fill="{cor}"/>')


def eixo_y(svg, valores, topo, esq, dir_, y_de, rotulo, fmt):
    for v in valores:
        y = y_de(v)
        cor = EIXO if v == 0 else GRADE
        svg.append(f'<line x1="{esq}" x2="{dir_}" y1="{y:.1f}" y2="{y:.1f}" stroke="{cor}" stroke-width="1"/>')
        svg.append(f'<text x="{esq - 8}" y="{y + 4:.1f}" text-anchor="end" class="t-eixo">{fmt(v)}</text>')
    meio = (y_de(0) + y_de(topo)) / 2
    svg.append(f'<text transform="translate(14,{meio:.1f}) rotate(-90)" text-anchor="middle" class="t-eixo">{rotulo}</text>')


def grafico_barras(grupos, rotulos_grupo, series, valor, larg=560, alt=380, topo_fixo=None,
                   rotulo_y="Tempo total (s)", com_valores=True, ref=None):
    """grupos: chaves; series: lista de (chave, nome); valor(grupo, serie) -> float ou None."""
    esq, dir_m, cima, baixo = 58, 12, 18, 46
    pw, ph = larg - esq - dir_m, alt - cima - baixo
    maximo = max(v for g in grupos for s, _ in series if (v := valor(g, s)) is not None)
    if ref:
        maximo = max(maximo, ref[0])
    valores_y, topo = ticks(topo_fixo or maximo * 1.12)
    y_de = lambda v: cima + ph - v / topo * ph
    svg = [f'<svg viewBox="0 0 {larg} {alt}" width="{larg}" height="{alt}" xmlns="http://www.w3.org/2000/svg">']
    eixo_y(svg, valores_y, topo, esq, larg - dir_m, y_de, rotulo_y, lambda v: num(v, 0 if v == int(v) else 1))
    banda = pw / len(grupos)
    for i, g in enumerate(grupos):
        presentes = [(s, valor(g, s)) for s, _ in series if valor(g, s) is not None]
        lb = min(40, (banda * 0.78 - 2 * (len(presentes) - 1)) / len(presentes))
        total = lb * len(presentes) + 2 * (len(presentes) - 1)
        x = esq + banda * i + (banda - total) / 2
        for s, v in presentes:
            svg.append(barra(x, y_de(v), lb, y_de(0), COR[s]))
            if com_valores:
                svg.append(f'<text x="{x + lb / 2:.1f}" y="{y_de(v) - 6:.1f}" text-anchor="middle" class="t-valor">{num(v)}</text>')
            x += lb + 2
        svg.append(f'<text x="{esq + banda * (i + 0.5):.1f}" y="{alt - baixo + 22}" text-anchor="middle" class="t-eixo">{rotulos_grupo[i]}</text>')
    if ref:
        y = y_de(ref[0])
        svg.append(f'<line x1="{esq}" x2="{larg - dir_m}" y1="{y:.1f}" y2="{y:.1f}" stroke="{TEXTO2}" stroke-width="1.5" stroke-dasharray="5 4"/>')
        svg.append(f'<text x="{larg - dir_m}" y="{y - 6:.1f}" text-anchor="end" class="t-ref">{ref[1]}</text>')
    svg.append("</svg>")
    return "\n".join(svg)


def grafico_speedup(dados, larg=620, alt=420):
    """Linhas de speedup (processos, threads) com a referência ideal y = x."""
    esq, dir_m, cima, baixo = 58, 120, 18, 46
    pw, ph = larg - esq - dir_m, alt - cima - baixo
    xs = [1, 2, 4, 8]
    x_de = lambda n: esq + n / 8 * pw          # eixo x linear: ideal vira uma reta
    valores_y, topo = ticks(8)
    y_de = lambda v: cima + ph - v / topo * ph
    svg = [f'<svg viewBox="0 0 {larg} {alt}" width="{larg}" height="{alt}" xmlns="http://www.w3.org/2000/svg">']
    eixo_y(svg, valores_y, topo, esq, esq + pw, y_de, "Speedup (×)", lambda v: num(v, 0))
    for n in xs:
        svg.append(f'<text x="{x_de(n):.1f}" y="{alt - baixo + 22}" text-anchor="middle" class="t-eixo">{n}</text>')
    svg.append(f'<text x="{esq + pw / 2:.1f}" y="{alt - 4}" text-anchor="middle" class="t-eixo">Trabalhadores (processos ou threads)</text>')
    # ideal
    svg.append(f'<line x1="{x_de(1):.1f}" y1="{y_de(1):.1f}" x2="{x_de(8):.1f}" y2="{y_de(8):.1f}" stroke="{MUDO}" stroke-width="1.5" stroke-dasharray="5 4"/>')
    svg.append(f'<text x="{x_de(8) + 8:.1f}" y="{y_de(8) + 4:.1f}" class="t-ref">ideal (8×)</text>')
    deslocamento = {"processos": 16, "threads": -8}
    for s in ("processos", "threads"):
        pts = [(x_de(n), y_de(dados[s][n])) for n in xs]
        svg.append(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts)}" fill="none" stroke="{COR[s]}" stroke-width="2"/>')
        for x, y in pts:
            svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{COR[s]}" stroke="{FUNDO}" stroke-width="2"/>')
        x, y = pts[-1]
        nome = "Processos" if s == "processos" else "Threads"
        svg.append(f'<text x="{x + 10:.1f}" y="{y + deslocamento[s]:.1f}" class="t-valor">{nome} {num(dados[s][8])}×</text>')
    svg.append("</svg>")
    return "\n".join(svg)


def legenda(itens, tracejado=None):
    partes = [f'<span class="leg"><i style="background:{COR[k]}"></i>{html.escape(n)}</span>' for k, n in itens]
    if tracejado:
        partes.append(f'<span class="leg"><i class="tracejado"></i>{html.escape(tracejado)}</span>')
    return '<div class="legenda">' + "".join(partes) + "</div>"


# ---------------------------------------------------------------- dados

fora = ler_csv(FORA)
dentro = ler_csv(DENTRO)

seq = next(r for r in fora if r["Versao"] == "Sequencial")
t_seq, io_seq = float(seq["Total_s"]), float(seq["IO_s"])
tempo = {(r["Versao"], int(r["Trabalhadores"])): float(r["Total_s"]) for r in fora}
speedup = {s: {1: 1.0, **{int(r["Trabalhadores"]): float(r["Speedup_Total"])
                          for r in fora if r["Versao"] == s}} for s in ("processos", "threads")}
tempo_d = {(r["Versao"], r["CPUs"], int(r["Trabalhadores"])): float(r["Total_s"]) for r in dentro}
sp_d = {(r["Versao"], r["CPUs"], int(r["Trabalhadores"])): float(r["Speedup_Total"]) for r in dentro}
iguais = sum(r["Imagem_Igual_Sequencial"] == "sim" for r in fora + dentro)
total_exec = len(fora) + len(dentro)

# Piora com 8 trabalhadores e 1 CPU, em relação ao sequencial com 1 CPU
seq1 = next(float(r["Total_s"]) for r in dentro if r["Versao"] == "Sequencial" and r["CPUs"] == "1")
pior_p = (tempo_d[("processos", "1", 8)] / seq1 - 1) * 100
pior_t = (tempo_d[("threads", "1", 8)] / seq1 - 1) * 100

# Lei de Amdahl com a fração serial medida (gravação da imagem no sequencial)
f_serial = io_seq / t_seq
amdahl = {n: 1 / (f_serial + (1 - f_serial) / n) for n in (2, 4, 8)}
amdahl8 = amdahl[8]

g1 = grafico_barras(
    [1, 2, 4, 8], ["1 (sequencial)", "2", "4", "8"],
    [("Sequencial", "Sequencial"), ("processos", "Processos"), ("threads", "Threads")],
    lambda g, s: (t_seq if s == "Sequencial" and g == 1 else
                  None if (s == "Sequencial") != (g == 1) else tempo[(s, g)]),
    larg=640, alt=420)
g2 = grafico_speedup(speedup)


def painel_container(versao):
    return grafico_barras(
        [2, 4, 8], ["2", "4", "8"],
        [("fora", "Fora"), ("1", "1 CPU"), ("2", "2 CPUs"), ("4", "4 CPUs")],
        lambda g, s: tempo[(versao, g)] if s == "fora" else tempo_d[(versao, s, g)],
        larg=520, alt=380, topo_fixo=16, com_valores=False,
        ref=(t_seq, f"sequencial fora: {num(t_seq)} s"))


g3p, g3t = painel_container("processos"), painel_container("threads")

(FONTE / "graficos").mkdir(exist_ok=True)
for nome, svg in [("grafico1_tempo", g1), ("grafico2_speedup", g2),
                  ("grafico3_container_processos", g3p), ("grafico3_container_threads", g3t)]:
    (FONTE / "graficos" / f"{nome}.svg").write_text(svg.replace(
        "<svg ", f'<svg style="font-family:Segoe UI,sans-serif;font-size:13px;fill:{TEXTO2}" ', 1), encoding="utf-8")

png = FONTE / "mandelbrot.png"
img = f'data:image/png;base64,{base64.b64encode(png.read_bytes()).decode()}' if png.exists() else ""


def tabela_container():
    linhas = []
    for cpus in ("1", "2", "4"):
        celulas = "".join(
            f"<td>{num(sp_d[('processos', cpus, n)])}× / {num(sp_d[('threads', cpus, n)])}×</td>" for n in (2, 4, 8))
        linhas.append(f"<tr><th>--cpus={cpus}</th>{celulas}</tr>")
    return ("<table class='tab'><tr><th>Speedup (proc / thr)</th><th>2</th><th>4</th><th>8</th></tr>"
            + "".join(linhas) + "</table>")


# ---------------------------------------------------------------- slides

slides = []


def slide(titulo, corpo, secao=""):
    slides.append((titulo, corpo, secao))


slide("", f"""
<div class="capa" style="background-image: linear-gradient(90deg, rgba(8,10,14,.96) 0%, rgba(8,10,14,.88) 42%, rgba(8,10,14,.15) 78%), url('{img}');">
  <p class="sobre">Faeterj-Petrópolis · Sistemas Operacionais II · Turma 2026/2 (noite)</p>
  <h1>Mandelbrot PPM</h1>
  <p class="sub">Programação paralela: uma aplicação sequencial transformada em versões com processos e com threads</p>
  <div class="autores">
    <p>Elton Giglio Kasesky<br>Frederico Bazano da Cruz</p>
    <p class="prof">Professor: Douglas Ericson</p>
  </div>
</div>""")

slide("O que é o conjunto de Mandelbrot?", """
<div class="duas">
<div>
<ul>
<li>Cada ponto do plano é um <b>número complexo</b> <code>c = a + b·i</code>: <code>a</code> é o eixo horizontal, <code>b</code> o vertical.</li>
<li>Para cada <code>c</code>, gera-se uma sequência:<br><code>z₀ = 0</code>, &nbsp;<code>zₙ₊₁ = zₙ² + c</code></li>
<li><code>c</code> <b>pertence ao conjunto</b> se essa sequência fica limitada, ou seja, nunca vai para o infinito.</li>
<li><b>Critério de fuga:</b> se em algum momento <code>|z| &gt; 2</code>, a sequência certamente diverge. Dá para parar ali: o ponto está <b>fora</b>.</li>
<li>Na prática, se não escapar em <code>MAX_ITERATIONS</code> (1000), considera-se que está <b>dentro</b>.</li>
<li>A borda é um <b>fractal</b>, com detalhe infinito. <b>Perto dela, a sequência demora muito para escapar</b>, e é isso que torna o custo dos pixels tão desigual.</li>
</ul>
</div>
<div>
<table class="tab exemplos">
<tr><th><code>c</code></th><th>sequência <code>z₁, z₂, z₃, …</code></th><th>resultado</th></tr>
<tr><td>0</td><td>0, 0, 0, …</td><td>dentro</td></tr>
<tr><td>−1</td><td>−1, 0, −1, 0, …</td><td>dentro (oscila)</td></tr>
<tr><td>i</td><td>i, −1+i, −i, −1+i, …</td><td>dentro (oscila)</td></tr>
<tr><td>1</td><td>1, 2, 5, …</td><td>fora em <b>3</b> iterações</td></tr>
<tr><td>0,5</td><td>0,5; 0,75; 1,06; 1,63; 3,15</td><td>fora em <b>5</b></td></tr>
<tr><td>0,3</td><td>0,3; 0,39; 0,45; 0,50; …</td><td>fora em <b>12</b></td></tr>
<tr><td>0,26</td><td>0,26; 0,33; 0,37; 0,40; …</td><td>fora em <b>30</b></td></tr>
<tr><td>0,251</td><td>0,251; 0,31; 0,35; 0,37; …</td><td>fora em <b>97</b></td></tr>
<tr><td>0,25</td><td>aproxima-se de 0,5</td><td>dentro (ponto da borda)</td></tr>
</table>
<p class="nota">Quanto mais perto da borda (aqui, de 0,25), mais iterações até decidir.</p>
</div>
</div>""", "1 · Problema original")

slide("Da matemática ao pixel", """
<div class="duas">
<div>
<ul>
<li><b>Pixel → ponto <code>c</code>:</b> a imagem é uma "janela" sobre o plano complexo. Cada pixel <code>(x, y)</code> vira um ponto <code>c</code> dessa janela.</li>
<li><b>Iterações → cor</b> (escape time): conta-se quantas iterações <code>z</code> levou para escapar.
  <ul>
  <li>escapa rápido (longe do conjunto): <b>escuro</b>;</li>
  <li>escapa devagar (perto da borda): <b>claro</b>, o efeito "neon";</li>
  <li>nunca escapa (dentro do conjunto): <b>preto</b>.</li>
  </ul></li>
<li><b>Coloração suave:</b> <code>i + 1 − log₂(log₂|z|)</code> acrescenta à contagem uma parte fracionária, que mede o quanto <code>z</code> passou do raio. Assim a cor varia continuamente, sem faixas.</li>
<li>Resultado: um tom de cinza por pixel, guardado como RGB (3 bytes).</li>
</ul>
</div>
<div>
<table class="tab exemplos">
<tr><th>Pixel (x, y)</th><th>Ponto c</th></tr>
<tr><td>canto superior esquerdo (0, 0)</td><td>≈ −2,67 + 1,2i</td></tr>
<tr><td>canto inferior direito (7679, 4319)</td><td>≈ 1,60 − 1,2i</td></tr>
<tr><td>janela vista</td><td>real de −2,67 a 1,60<br>imaginário de −1,2 a 1,2</td></tr>
</table>
<p class="nota">O conjunto ocupa o real de −2 a ≈0,47 e o imaginário de −1,12 a 1,12: a janela enquadra o conjunto inteiro com margem.</p>
</div>
</div>""", "1 · Problema original")

slide("Formato de imagem PPM (P6)", """
<div class="duas">
<div>
<ul>
<li><b>Simples:</b> um cabeçalho em texto (<code>P6</code>, largura, altura, valor máximo 255) seguido dos bytes RGB crus, linha a linha, 3 bytes por pixel. Sem compressão.</li>
<li><b>Portátil:</b> formato aberto do Netpbm, lido por visualizadores e editores comuns (GIMP, ImageMagick, IrfanView…).</li>
<li><b>Sem bibliotecas externas:</b> basta <code>stdio.h</code>. Não há dependência para instalar, nem no container.</li>
<li>A <code>struct Color</code> é <code>packed</code> (exatamente 3 bytes, sem preenchimento), então o framebuffer na memória já tem o <b>mesmo layout do arquivo</b>: a imagem inteira é gravada com <b>um único <code>fwrite</code></b>.</li>
<li>Custo: arquivo grande (≈ 95 MB em 8K), mas a gravação leva só ≈ 0,02 s.</li>
</ul>
</div>
<pre class="pequeno"><code>typedef struct {
    unsigned char r, g, b;
} __attribute__((packed)) Color;

void writeImage(Color *frameBuffer, int width,
                int height, const char *outputFile) {
    FILE *file = fopen(outputFile, "wb");
    if (!file) { perror("..."); return; }

    // cabeçalho em texto
    fprintf(file, "P6\\n");
    fprintf(file, "%d %d\\n", width, height);
    fprintf(file, "255\\n");

    // pixels: bytes RGB crus, de uma vez só
    size_t totalPixels = (size_t)width * height;
    fwrite(frameBuffer, sizeof(Color), totalPixels, file);

    fclose(file);
}</code></pre>
</div>""", "1 · Problema original")

slide("Pixel shader: do pixel ao ponto <code>c</code>", """
<div class="duas">
<div>
<ul class="compacta">
<li>Função que calcula a cor de <b>um pixel</b> só a partir das suas coordenadas, como um <b>pixel shader</b> de GPU. Por isso os pixels são independentes.</li>
<li><b>Inversão do eixo y:</b> na imagem, y cresce para baixo; no plano, o eixo imaginário cresce para cima.</li>
<li><b>Panning:</b> desloca a janela em 1/8 da largura para centralizar o conjunto, que fica mais à esquerda (real de −2 a 0,47).</li>
<li><b>Normalização 0 a 1:</b> <code>u = x / width</code>, <code>v = y / height</code>, independente da resolução.</li>
<li><b>Normalização −1 a 1:</b> <code>2u − 1</code>, centralizando a origem.</li>
<li><b>Aspect ratio:</b> o eixo x é multiplicado por 16/9, para o pixel ser quadrado e o fractal não ficar achatado.</li>
<li><b>Zoom 1,2:</b> amplia a janela em 20%, para o conjunto caber com margem.</li>
<li>Comum às três versões, em <code>comum/mandelbrot.c</code>, junto com <code>renderRow</code> (uma linha), <code>writeImage</code> e <code>getTimeSec</code>.</li>
</ul>
</div>
<pre class="pequeno"><code>Color pixelShader(int x, int y, int width, int height) {
    double aspectRatio = (double) width / height;
    y = height - y;              // inverte o eixo y
    x = x - width / 8;           // panning horizontal
    double u = ((double) x / width);    // 0 a 1
    double v = ((double) y / height);
    // -1 a 1, aspect ratio e zoom: c = cx + cy·i
    double cx = (((2.0f * u) - 1.0f) * aspectRatio) * 1.2;
    double cy = ((2.0f * v) - 1.0f) * 1.2;

    double zx = 0, zy = 0;       // z = 0
    for (int i = 0; i &lt; MAX_ITERATIONS; i++) {
        double temp_zx = zx*zx - zy*zy + cx;   // z = z² + c
        double temp_zy = 2*zx*zy + cy;
        zx = temp_zx;  zy = temp_zy;
        double squaredDistance = zx*zx + zy*zy;
        if (squaredDistance &gt; 4.0) {           // |z| &gt; 2
            double smooth = i + 1.0
                - log2(log2(sqrt(squaredDistance)));
            return colorf(smooth / 100.0, ...);
        }
    }
    return colorf(0.0, 0.0, 0.0);             // dentro: preto
}</code></pre>
</div>""", "1 · Problema original")

slide("Entrada e versão sequencial", f"""
<div class="duas">
<div>
<h3>Entrada: o parâmetro <code>factor</code></h3>
<ul>
<li>A resolução é <code>16·factor × 9·factor</code>: sempre <b>16:9 exato</b> e sempre <b>inteira</b>.</li>
<li>Com uma largura qualquer, a altura poderia sair fracionária (1000 × 562,5). Com o <code>factor</code>, não: 120 → 1920 × 1080 (Full HD), 240 → 3840 × 2160 (4K), <b>480 → 7680 × 4320 (8K)</b>.</li>
<li>Um único número controla a carga de trabalho, que cresce com <code>factor²</code>. Nos testes: <code>factor = 480</code>, cerca de <b>33 milhões de pixels</b>.</li>
</ul>
<h3>Versão sequencial</h3>
<ul>
<li>Um único fluxo calcula as linhas de cima para baixo e depois grava a imagem.</li>
<li>Tempo: <b>{num(t_seq)} s</b> (cálculo {num(float(seq['Calculo_s']))} s + gravação {num(io_seq, 3)} s). É a referência para o speedup e para a imagem.</li>
</ul>
</div>
<div>
<pre><code>int width  = 16 * factor;
int height =  9 * factor;

for (int y = 0; y &lt; height; y++)
    renderRow(frameBuffer, y, width, height);

writeImage(frameBuffer, width, height, arquivo);</code></pre>
<p class="nota">Demonstração:</p>
<pre><code>./bin/sequencial out/sequencial.ppm 480</code></pre>
</div>
</div>""", "2 · Versão sequencial")

slide("Estratégia de paralelização: como dividir o trabalho?", """
<ul>
<li>Renderizar é <b>naturalmente paralelizável</b>: cada pixel depende só das próprias coordenadas.</li>
<li>Mas o <b>custo de cada pixel varia muito</b>: pontos longe do conjunto escapam em poucas iterações; pontos dentro dele vão até 1000. O laço tem desvios (branching) e número de iterações variável.</li>
</ul>
<table class="tab">
<tr><th>Divisão</th><th>Granularidade</th><th>Balanceamento</th><th>Sincronização</th></tr>
<tr><td>Setores contínuos</td><td>N faixas</td><td>ruim: a faixa central concentra o conjunto</td><td>nenhuma</td></tr>
<tr><td>Round-robin de linhas</td><td>linhas intercaladas, fixas</td><td>bom, em média</td><td>nenhuma (sem coordenação entre trabalhadores)</td></tr>
<tr><td>Pixel a pixel (fila)</td><td>33 milhões de tarefas</td><td>ótimo</td><td>uma por pixel: overhead enorme frente ao trabalho de um pixel</td></tr>
<tr class="destaque"><td><b>Fila de linhas (escolhida)</b></td><td>4320 linhas</td><td>adapta-se sozinho</td><td>uma por linha: 4320 no total, desprezível</td></tr>
</table>""", "3 · Estratégia de paralelização")

slide("Fila de trabalho dinâmica, linha a linha", """
<div class="duas">
<div>
<ul class="compacta">
<li>A "fila" é um contador compartilhado: <code>next_row</code>, a próxima linha ainda não calculada.</li>
<li>Cada trabalhador repete: <b>pegar uma linha → calcular → pegar a próxima</b>, até a fila acabar. Quem pega linhas leves processa mais linhas, e todos terminam quase juntos.</li>
<li><b>Condição de corrida evitada:</b> <code>next_row++</code> não é uma operação única. São três passos: <b>ler</b>, <b>somar 1</b> e <b>gravar</b>. Sem exclusão mútua, dois trabalhadores podem se intercalar:</li>
</ul>
<table class="tab exemplos corrida">
<tr><th>Trabalhador A</th><th>Trabalhador B</th><th><code>next_row</code></th></tr>
<tr><td>lê 10</td><td></td><td>10</td></tr>
<tr><td></td><td>lê 10</td><td>10</td></tr>
<tr><td>grava 11, calcula a linha 10</td><td></td><td>11</td></tr>
<tr><td></td><td>grava 11, calcula a linha <b>10 de novo</b></td><td>11</td></tr>
</table>
<p class="nota">Resultado: trabalho duplicado e um incremento perdido. Com o lock, ler e incrementar viram uma operação indivisível, e cada linha é entregue a <b>exatamente um</b> trabalhador.</p>
</div>
<div>
<pre><code>for (;;) {
    lock();                  // mutex ou semáforo
    int y = next_row++;      // região crítica
    unlock();

    if (y &gt;= height) break;  // fila vazia

    renderRow(frameBuffer, y, width, height);
}</code></pre>
<p class="nota"><b>Escrita sem lock:</b> como cada linha tem um único dono, as escritas no framebuffer nunca se sobrepõem.</p>
</div>
</div>""", "3 · Estratégia de paralelização")

slide("Implementação com processos", """
<div class="duas">
<div>
<ul>
<li>O pai lê o número de processos da linha de comando e cria os filhos com <code>fork()</code>.</li>
<li>Cada filho executa o laço da fila e termina com <code>_exit(0)</code>.
  <ul><li><code>_exit</code>, e não <code>exit</code>: evita que cada filho descarregue de novo o buffer do <code>printf</code> herdado do pai.</li></ul></li>
<li>O pai espera todos com <code>waitpid()</code>, sem deixar zumbis, e só então grava a imagem.</li>
<li>Os processos não compartilham memória por padrão: framebuffer e fila precisam ser <b>explicitamente compartilhados</b>.</li>
</ul>
</div>
<pre><code>for (p = 0; p &lt; num_processes; p++) {
    pids[p] = fork();
    if (pids[p] == 0) {          // filho
        /* laço da fila */
        _exit(0);
    }
}
for (p = 0; p &lt; num_processes; p++)
    waitpid(pids[p], NULL, 0);   // pai

writeImage(frameBuffer, ...);</code></pre>
</div>""", "4 · Implementação com processos")

slide("Memória compartilhada", """
<div class="duas">
<div>
<ul>
<li>Duas regiões criadas com <code>mmap(MAP_SHARED | MAP_ANONYMOUS)</code> <b>antes do fork</b>, herdadas por todos os filhos:
  <ul>
  <li><b>framebuffer</b>: a imagem (cerca de 95 MB em 8K), escrita pelos filhos e gravada pelo pai;</li>
  <li><b>SharedState</b>: a fila (<code>next_row</code>) e o semáforo.</li>
  </ul></li>
<li>Sem <code>MAP_SHARED</code>, o fork daria a cada filho uma <b>cópia própria</b> (copy-on-write): o pai receberia a imagem vazia e cada filho teria sua própria fila.</li>
<li>Nas threads, isso é automático: todas compartilham o espaço de endereçamento do processo.</li>
</ul>
</div>
<pre><code>typedef struct {
    sem_t sem_lock;
    int   next_row;
} SharedState;

Color *frameBuffer = mmap(NULL, fb_size,
        PROT_READ | PROT_WRITE,
        MAP_SHARED | MAP_ANONYMOUS, -1, 0);

SharedState *shared = mmap(NULL, sizeof(SharedState),
        PROT_READ | PROT_WRITE,
        MAP_SHARED | MAP_ANONYMOUS, -1, 0);</code></pre>
</div>""", "5 · Memória compartilhada")

slide("Sincronização", """
<div class="duas">
<div>
<ul>
<li>A única região crítica é pegar a próxima linha: <code>y = next_row++</code>.</li>
<li><b>Processos:</b> semáforo POSIX <b>binário</b>, compartilhado entre processos:
  <code>sem_init(&amp;sem, pshared=1, valor=1)</code>. Na prática, funciona como um mutex entre processos.</li>
<li><b>Threads:</b> <code>pthread_mutex_t</code>.</li>
<li><b>Mutex × semáforo:</b> o mutex tem dono (só quem trava destrava); o semáforo é um contador (qualquer um pode dar <code>sem_post</code>). Com valor inicial 1, os dois garantem exclusão mútua.</li>
<li><b>Por que semáforo nos processos:</b> o <code>pshared=1</code> do <code>sem_init</code> é o jeito direto de compartilhar entre processos. Um mutex também funcionaria, mas exigiria o atributo <code>PTHREAD_PROCESS_SHARED</code>.</li>
<li><b>Custo:</b> 4320 entradas na região crítica em todo o programa, desprezível frente a cerca de 10 s de cálculo.</li>
</ul>
</div>
<pre><code>// processos
sem_wait(&amp;shared-&gt;sem_lock);
int y = shared-&gt;next_row++;
sem_post(&amp;shared-&gt;sem_lock);

// threads
pthread_mutex_lock(&amp;q-&gt;mutex);
int y = q-&gt;next_row++;
pthread_mutex_unlock(&amp;q-&gt;mutex);</code></pre>
</div>""", "6 · Sincronização")

slide("Implementação com threads", """
<div class="duas">
<div>
<ul>
<li>A thread principal lê o número de threads da linha de comando, cria as threads com <code>pthread_create()</code> e espera todas com <code>pthread_join()</code>.</li>
<li>Todas recebem um ponteiro para a mesma <code>WorkQueue</code>: fila, mutex e framebuffer.</li>
<li><b>Memória compartilhada sem esforço:</b> o framebuffer é um <code>malloc</code> comum, visível a todas as threads do processo.</li>
<li>O mesmo laço da fila da versão com processos, com mutex no lugar do semáforo.</li>
</ul>
</div>
<pre><code>typedef struct {
    int next_row;
    pthread_mutex_t mutex;
    int width, height;
    Color *frameBuffer;
} WorkQueue;

for (t = 0; t &lt; num_threads; t++)
    pthread_create(&amp;threads[t], NULL,
                   threadWorker, &amp;queue);
for (t = 0; t &lt; num_threads; t++)
    pthread_join(threads[t], NULL);</code></pre>
</div>""", "7 · Implementação com threads")

slide("Container e limite de CPU", """
<div class="duas">
<div>
<ul>
<li><code>container/Dockerfile</code>: Ubuntu 24.04 + <code>build-essential</code>; copia o código, roda <code>make</code> e coloca os programas no <code>PATH</code>.</li>
<li>Não é preciso instalar nada no sistema, só ter o Docker.</li>
<li><code>--cpus=N</code> <b>não</b> reduz os núcleos visíveis (o container continua vendo 8). Ele limita o <b>tempo de CPU</b> do grupo: N × 100 ms de CPU a cada janela de 100 ms (cota do escalonador CFS via cgroups).</li>
<li>Quando a cota acaba, todos os processos/threads do container ficam pausados até a próxima janela (<i>throttling</i>).</li>
</ul>
</div>
<pre><code>docker build -t mandelbrot -f container/Dockerfile .

docker run --rm --cpus="2" mandelbrot \\
       processos 4 imagem.ppm 480</code></pre>
</div>""", "Container")

slide("Metodologia dos experimentos", f"""
<ul>
<li><b>Máquina:</b> Intel Core i5-12600K, WSL2 (Ubuntu 22.04) com 8 CPUs lógicas; gcc 11.4 <code>-O3</code>; Docker 29.9.2.</li>
<li><b>Entrada:</b> <code>factor=480</code> (7680 × 4320); <b>média de 3 execuções</b> por configuração.</li>
<li><b>Fora do container</b> (<code>testes/executar_testes.sh</code>): sequencial; processos e threads com 2, 4 e 8.</li>
<li><b>Dentro do container</b> (<code>testes/executar_testes_docker.sh</code>): sequencial, processos e threads com 2, 4 e 8, para cada limite <code>--cpus</code> = 1, 2 e 4.</li>
<li><b>Speedup</b> = tempo do sequencial ÷ tempo da versão paralela (dentro do container, o sequencial com o mesmo limite).</li>
<li><b>Corretude:</b> cada imagem é comparada byte a byte com a do sequencial: <b>{iguais} de {total_exec} execuções idênticas</b>.</li>
<li>Resultados congelados em <code>testes/resultados/final_*.csv</code>.</li>
</ul>""", "8 · Resultados experimentais")

slide("Gráfico 1: tempo de execução (fora do container)", f"""
<div class="grafico">
<div>{legenda([("Sequencial", "Sequencial"), ("processos", "Processos"), ("threads", "Threads")])}{g1}</div>
<div class="lateral">
<ul>
<li>Dobrar os trabalhadores quase divide o tempo pela metade até 4.</li>
<li>De 4 para 8, o ganho continua, mas menor.</li>
<li>Processos e threads ficam praticamente empatados.</li>
</ul>
</div>
</div>""", "8 · Resultados experimentais")

slide("Gráfico 2: speedup (fora do container)", f"""
<div class="grafico">
<div>{legenda([("processos", "Processos"), ("threads", "Threads")], "Ideal (linear)")}{g2}</div>
<div class="lateral">
<ul>
<li>2 trabalhadores: {num(speedup['processos'][2])}× e {num(speedup['threads'][2])}×, quase ideal.</li>
<li>4: {num(speedup['processos'][4])}× e {num(speedup['threads'][4])}×.</li>
<li>8: {num(speedup['processos'][8])}× e {num(speedup['threads'][8])}×, longe dos 8×.</li>
<li>A curva se afasta da ideal conforme cresce o número de trabalhadores. A explicação está nas conclusões.</li>
</ul>
</div>
</div>""", "8 · Resultados experimentais")

slide("Gráfico 3: fora × dentro do container", f"""
{legenda([("fora", "Fora do container"), ("1", "--cpus=1"), ("2", "--cpus=2"), ("4", "--cpus=4")], "Sequencial (fora)")}
<div class="paineis">
<div><h3>Processos</h3>{g3p}<p class="eixo-x">Trabalhadores</p></div>
<div><h3>Threads</h3>{g3t}<p class="eixo-x">Trabalhadores</p></div>
</div>""", "8 · Resultados experimentais")

slide("Dentro do container: speedup por limite de CPU", f"""
<div class="duas">
<div>{tabela_container()}
<p class="nota">Speedup em relação ao sequencial com o mesmo limite de CPU.</p></div>
<div>
<ul>
<li><b>O ganho é limitado pelas CPUs disponíveis</b>: nunca passa do limite, e o melhor caso é um trabalhador por CPU.</li>
<li><b>Mais trabalhadores que CPUs piora o tempo</b>: com 1 CPU, 8 trabalhadores levam {num(pior_p, 0)}% (processos) e {num(pior_t, 0)}% (threads) a mais que o sequencial.</li>
<li><b>O próprio limite tem custo</b>: com 2 trabalhadores e 2 CPUs, o speedup é {num(sp_d[('processos', '2', 2)])}×, contra {num(speedup['processos'][2])}× fora do container.</li>
</ul>
</div>
</div>""", "8 · Resultados experimentais")

slide("Comparação entre as três versões", f"""
<table class="tab">
<tr><th></th><th>Sequencial</th><th>Processos</th><th>Threads</th></tr>
<tr><th>Fluxos de execução</th><td>1</td><td>N processos (<code>fork</code>)</td><td>N threads (<code>pthread_create</code>)</td></tr>
<tr><th>Memória da imagem</th><td><code>malloc</code></td><td><code>mmap(MAP_SHARED)</code>, explícita</td><td><code>malloc</code>, compartilhada naturalmente</td></tr>
<tr><th>Sincronização</th><td>nenhuma</td><td>semáforo binário (<code>pshared=1</code>)</td><td><code>pthread_mutex_t</code></td></tr>
<tr><th>Espera pelo fim</th><td>-</td><td><code>waitpid</code></td><td><code>pthread_join</code></td></tr>
<tr><th>Tempo com 8 trabalhadores</th><td>{num(t_seq)} s</td><td>{num(tempo[('processos', 8)])} s ({num(speedup['processos'][8])}×)</td><td>{num(tempo[('threads', 8)])} s ({num(speedup['threads'][8])}×)</td></tr>
<tr><th>Imagem gerada</th><td colspan="3">idêntica byte a byte nas três</td></tr>
</table>
<p class="nota">Processos e threads empatam porque toda a comunicação é pegar a próxima linha (4320 vezes) e escrever em memória compartilhada sem lock. O custo extra do <code>fork</code> e do semáforo entre processos não aparece frente a cerca de 10 s de cálculo.</p>
""", "9 · Comparação entre as três versões")

slide("Lei de Amdahl: qual speedup seria possível?", f"""
<div class="duas">
<div>
<ul>
<li>Todo programa tem uma parte que <b>só roda em sequência</b> (fração <code>f</code>) e uma parte <b>paralelizável</b> (<code>1 − f</code>). Com <code>N</code> trabalhadores, só a parte paralelizável fica <code>N</code> vezes mais rápida:</li>
</ul>
<p class="formula">S(N) = 1 / ( f + (1 − f) / N )</p>
<ul>
<li>A parte serial limita o ganho: mesmo com infinitos trabalhadores, <code>S ≤ 1 / f</code>. Por isso o teórico fica <b>sempre abaixo de N</b>.</li>
<li><b>Aqui, a parte serial é a gravação da imagem</b>, feita só pelo processo/thread principal:<br>
<code>f = {num(io_seq, 4)} s ÷ {num(t_seq, 4)} s ≈ {num(f_serial, 5)}</code> ({num(f_serial * 100, 3)}%), com teto <code>1 / f ≈ {num(1 / f_serial, 0)}×</code></li>
<li>Para 8 trabalhadores: <code>S(8) = 1 / ({num(f_serial, 5)} + {num(1 - f_serial, 5)} / 8) ≈ {num(amdahl8, 3)}×</code>.</li>
</ul>
</div>
<div>
<table class="tab">
<tr><th>Trabalhadores</th><th>Amdahl (teórico)</th><th>Medido (proc / thr)</th></tr>
<tr><td>2</td><td>{num(amdahl[2], 3)}×</td><td>{num(speedup['processos'][2])}× / {num(speedup['threads'][2])}×</td></tr>
<tr><td>4</td><td>{num(amdahl[4], 3)}×</td><td>{num(speedup['processos'][4])}× / {num(speedup['threads'][4])}×</td></tr>
<tr><td>8</td><td>{num(amdahl[8], 3)}×</td><td>{num(speedup['processos'][8])}× / {num(speedup['threads'][8])}×</td></tr>
</table>
<p class="nota">O teórico fica um pouco abaixo de N (1,996× e não 2×) por causa da parte serial. Até 4 trabalhadores, o medido fica perto do teórico. Com 8, fica bem abaixo: <b>a diferença não é explicada pela parte serial</b>, que é mínima. A causa está no hardware (próximo slide).</p>
</div>
</div>""", "10 · Conclusões")

slide("Conclusões", f"""
<ul class="conclusoes">
<li><b>A parte serial é mínima</b> ({num(f_serial * 100)}%, a gravação da imagem). A Lei de Amdahl permitiria {num(amdahl8, 2)}× com 8 trabalhadores, e medimos {num(speedup['threads'][8])}×: <b>a perda não vem da parte serial</b>.</li>
<li><b>O speedup não é linear por causa do hardware.</b> As 8 CPUs lógicas do WSL não são 8 núcleos iguais e independentes: há hyperthreading (dois fluxos dividindo um núcleo) e núcleos P/E no i5-12600K, e a frequência de turbo cai quando mais núcleos estão ativos.</li>
<li><b>A divisão dinâmica funciona:</b> com a fila de linhas, os trabalhadores terminam juntos mesmo com custo por linha muito desigual.</li>
<li><b>Processos ≈ threads:</b> como os dois usam memória compartilhada e uma região crítica mínima, o mecanismo quase não pesa. A diferença de custo entre eles (criação, troca de contexto) desaparece frente ao cálculo.</li>
<li><b>Docker:</b> sem limite apertando, o container tem desempenho praticamente igual à execução direta. O <code>--cpus</code> limita o ganho ao número de CPUs da cota e tem um pequeno custo próprio (pausas de throttling).</li>
<li><b>Mais trabalhadores que núcleos degrada o desempenho:</b> mais trocas de contexto e cota consumida por fluxos que dividem o mesmo núcleo. O número de trabalhadores deve acompanhar a CPU disponível.</li>
</ul>""", "10 · Conclusões")

slide("", f'<img class="tela-cheia" src="{img}" alt="Fractal de Mandelbrot gerado pela aplicação">')

# ---------------------------------------------------------------- HTML

CSS = f"""
@page {{ size: 1280px 720px; margin: 0; }}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; background: #d9d8d2; }}
body {{ font-family: "Segoe UI", system-ui, sans-serif; color: {TEXTO}; }}
.slide {{ width: 1280px; height: 720px; background: {FUNDO}; position: relative; overflow: hidden;
          padding: 56px 72px 48px; page-break-after: always; break-after: page; margin: 0 auto 24px; }}
@media print {{ body {{ background: none; }} .slide {{ margin: 0; }} }}
.secao {{ font-size: 15px; letter-spacing: .04em; text-transform: uppercase; color: #256abf; font-weight: 600; margin: 0 0 6px; }}
h2 {{ font-size: 36px; margin: 0 0 24px; font-weight: 650; }}
h3 {{ font-size: 21px; margin: 6px 0 8px; font-weight: 650; }}
ul {{ margin: 0; padding-left: 26px; font-size: 21px; line-height: 1.42; }}
ul ul {{ font-size: 18px; margin-top: 4px; }}
li {{ margin-bottom: 9px; }}
code {{ font-family: "Cascadia Code", Consolas, monospace; font-size: .88em; background: #f0efec; padding: 1px 5px; border-radius: 4px; }}
pre {{ margin: 0; background: #1f2430; color: #e8e6df; border-radius: 10px; padding: 20px 22px; font-size: 16px; line-height: 1.5; }}
pre code {{ background: none; padding: 0; font-size: inherit; color: inherit; }}
.duas {{ display: grid; grid-template-columns: 1.15fr 1fr; gap: 40px; align-items: start; }}
.duas > pre {{ align-self: center; }}
.fractal {{ width: 100%; border-radius: 10px; align-self: center; }}
.nota {{ font-size: 17px; color: {TEXTO2}; margin: 16px 0 8px; }}
.tab {{ border-collapse: collapse; width: 100%; font-size: 18px; margin-top: 22px; }}
.tab th, .tab td {{ border-bottom: 1px solid {GRADE}; padding: 9px 12px; text-align: left; vertical-align: top; }}
.tab tr:first-child th {{ border-bottom: 2px solid {EIXO}; color: {TEXTO2}; font-weight: 600; }}
.tab .destaque td {{ background: #e8f1fc; }}
.grafico {{ display: grid; grid-template-columns: 650px 1fr; gap: 32px; align-items: center; }}
.lateral ul {{ font-size: 19px; }}
.legenda {{ display: flex; gap: 22px; font-size: 16px; color: {TEXTO2}; margin: 0 0 6px 58px; flex-wrap: wrap; }}
.leg i {{ display: inline-block; width: 14px; height: 14px; border-radius: 3px; margin-right: 7px; vertical-align: -2px; }}
.leg i.tracejado {{ height: 0; border-top: 2px dashed {TEXTO2}; border-radius: 0; vertical-align: 4px; width: 22px; }}
.paineis {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }}
.paineis h3 {{ margin: 4px 0 0 58px; }}
.eixo-x {{ text-align: center; font-size: 14px; color: {TEXTO2}; margin: -8px 0 0 46px; }}
svg {{ font-family: "Segoe UI", system-ui, sans-serif; }}
.t-eixo {{ font-size: 14px; fill: {TEXTO2}; }}
.t-valor {{ font-size: 13px; fill: {TEXTO}; font-weight: 600; }}
.t-ref {{ font-size: 13px; fill: {TEXTO2}; }}
.conclusoes {{ font-size: 19px; line-height: 1.38; }}
.conclusoes li {{ margin-bottom: 11px; }}
.capa {{ position: absolute; inset: 0; padding: 0 72px; display: flex; flex-direction: column; justify-content: center;
          background-size: cover; background-position: center right; color: #f0efec; }}
.capa h1 {{ font-size: 72px; margin: 10px 0 14px; color: #ffffff; }}
.sobre {{ font-size: 17px; color: #86b6ef; font-weight: 600; text-transform: uppercase; letter-spacing: .04em; margin: 0; }}
.sub {{ font-size: 24px; color: #c3c2b7; line-height: 1.35; margin: 0 0 56px; max-width: 620px; }}
.autores p {{ font-size: 22px; line-height: 1.5; margin: 0 0 14px; color: #f0efec; }}
.autores .prof {{ font-size: 18px; color: #c3c2b7; }}
.exemplos {{ font-size: 16px; margin-top: 0; }}
.exemplos td, .exemplos th {{ padding: 6px 10px; }}
.pequeno {{ font-size: 13px; line-height: 1.42; padding: 14px 16px; }}
.compacta {{ font-size: 19px; line-height: 1.36; }}
.compacta li {{ margin-bottom: 7px; }}
.corrida {{ margin: 6px 0 0 26px; width: calc(100% - 26px); font-size: 15px; }}
.formula {{ font-family: "Cambria Math", Cambria, serif; font-size: 30px; text-align: center; margin: 14px 0 18px; }}
.tela-cheia {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }}
.num {{ position: absolute; right: 36px; bottom: 22px; font-size: 14px; color: {MUDO}; }}
"""

partes = []
for i, (titulo, corpo, secao) in enumerate(slides, 1):
    cab = (f'<p class="secao">{secao}</p>' if secao else "") + (f"<h2>{titulo}</h2>" if titulo else "")
    rodape = f'<span class="num">{i} / {len(slides)}</span>' if titulo else ""
    partes.append(f'<section class="slide">{cab}{corpo}{rodape}</section>')

saida = FONTE / "apresentacao.html"
saida.write_text(f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<title>Mandelbrot PPM — Programação Paralela</title>
<style>{CSS}</style></head>
<body>
{chr(10).join(partes)}
</body></html>
""", encoding="utf-8")
print(f"{len(slides)} slides -> {saida.relative_to(RAIZ)}")
