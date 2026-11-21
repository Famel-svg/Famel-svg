"""Fundo animado do README em imagens: grade neon com varredura ao abrir, depois chuva de código.

O README é uma pilha de imagens sem espaço entre si (ver scripts/build_readme.py). Cada peça
desenha a sua fatia do mesmo fundo, em coordenadas de referência: a página tem 860 de largura
e cada peça sabe onde começa (x0, y0). Assim a grade fica alinhada entre peças e a linha de
varredura desce pela página inteira, passando de uma imagem para a próxima.

As posições ficam em data/readme-layout.json (gerado por build_readme.py), para que os
geradores diários (build_cards.py) refaçam city-panel.svg e overview-panel.svg no lugar certo.

Uso: python scripts/panel.py assets/city.svg [...]  -> grava assets/city-panel.svg
"""
import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LAYOUT = ROOT / "data" / "readme-layout.json"
REF_W, CARD, GAP = 860, 812, 16  # largura da página, largura do cartão, respiro embaixo
BASE = "#04070f"
MONO = "ui-monospace,'SF Mono',Menlo,Consolas,monospace"
GRID = 40          # passo da grade
SPEED = 1100       # velocidade da varredura (unidades de referência por segundo)
START = 0.6        # atraso antes da varredura começar
COLS = 26          # passo das colunas da chuva
GLYPHS = "01{}<>/;=λ"


def layout():
    try:
        return json.loads(LAYOUT.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def background(w, h, x0, y0, seed):
    """Fatia (w x h) do fundo da página que começa em (x0, y0). Retorna (defs, corpo)."""
    rnd = random.Random(seed)
    t_grid = START + (y0 + h) / SPEED          # a varredura terminou de passar por esta peça
    scan_dur = (h + 120) / SPEED

    # grade alinhada à página inteira
    xs = [x for x in range(0, REF_W + 1, GRID) if x0 <= x <= x0 + w]
    ys = [y for y in range(0, int(y0 + h) + GRID, GRID) if y0 <= y <= y0 + h]
    lines = "".join(f'<line x1="{x - x0}" y1="0" x2="{x - x0}" y2="{h:.1f}"/>' for x in xs)
    lines += "".join(f'<line x1="0" y1="{y - y0:.1f}" x2="{w}" y2="{y - y0:.1f}"/>' for y in ys)
    dots = ""
    for x in xs:
        for y in ys:
            r = random.Random(x * 7919 + y)
            if r.random() < 0.06:
                d = r.uniform(2, 5)
                dots += (f'<circle cx="{x - x0}" cy="{y - y0:.1f}" r="2" fill="{r.choice(("#58a6ff", "#3fb950"))}">'
                         f'<animate attributeName="opacity" values="0;1;0" dur="{d:.1f}s" begin="{r.uniform(0, d):.1f}s" repeatCount="indefinite"/></circle>')

    # chuva: 6 colunas-modelo reaproveitadas com <use>
    defs = ('<linearGradient id="scan" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#58a6ff" stop-opacity="0"/>'
            '<stop offset=".9" stop-color="#58a6ff" stop-opacity=".35"/><stop offset="1" stop-color="#9ecbff" stop-opacity=".9"/></linearGradient>')
    for i in range(6):
        r = random.Random(i)
        spans = "".join(f'<tspan x="0" dy="18" fill-opacity="{(k + 1) / 10:.1f}">{escape_glyph(r.choice(GLYPHS))}</tspan>' for k in range(10))
        defs += f'<text id="rc{i}" font-family="{MONO}" font-size="14">{spans}</text>'
    rain = ""
    for i in range(REF_W // COLS + 1):
        x = 13 + i * COLS
        if not x0 - 8 <= x <= x0 + w:
            continue
        d = rnd.uniform(4, 9) * max(1.0, (h + 200) / 400)
        col = "#3fb950" if rnd.random() < 0.3 else "#58a6ff"
        rain += (f'<use href="#rc{rnd.randrange(6)}" x="{x - x0}" fill="{col}">'
                 f'<animateTransform attributeName="transform" type="translate" values="0 -200;0 {h + 20:.0f}" '
                 f'dur="{d:.1f}s" begin="-{rnd.uniform(0, d):.1f}s" repeatCount="indefinite"/></use>')

    body = (f'<rect width="{w}" height="{h:.1f}" fill="{BASE}"/>'
            f'<g opacity="1"><g stroke="#58a6ff" stroke-opacity=".16" stroke-width="1">{lines}</g>{dots}'
            f'<animate attributeName="opacity" to=".25" begin="{t_grid:.2f}s" dur="1.2s" fill="freeze"/></g>'
            f'<g opacity="0">{rain}'
            f'<animate attributeName="opacity" to=".55" begin="{t_grid + .2:.2f}s" dur="1.5s" fill="freeze"/></g>'
            f'<rect x="0" y="-120" width="{w}" height="120" fill="url(#scan)">'
            f'<animate attributeName="y" from="-120" to="{h:.1f}" begin="{START + y0 / SPEED:.2f}s" dur="{scan_dur:.2f}s" fill="freeze"/></rect>')
    return defs, body


def escape_glyph(c):
    return {"<": "&lt;", ">": "&gt;", "&": "&amp;"}.get(c, c)


def wrap(svg, name, y0):
    """Põe o SVG (um cartão) dentro da sua fatia de fundo, com margens laterais e respiro embaixo."""
    m = re.search(r'<svg\b[^>]*\bwidth="([\d.]+)"[^>]*\bheight="([\d.]+)"', svg)
    w, h = float(m.group(1)), float(m.group(2))
    k = w / CARD
    mx, gap = (REF_W - CARD) / 2 * k, GAP * k
    W, H = w + 2 * mx, h + gap
    label = re.search(r'aria-label="([^"]*)"', svg)
    aria = f' aria-label="{label.group(1)}"' if label else ""
    inner = re.sub(r"^<svg\b", f'<svg x="{mx:.2f}" y="0"', svg.strip(), count=1)
    defs, body = background(REF_W, H / k, 0, y0, name)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.2f}" height="{H:.2f}" '
            f'viewBox="0 0 {W:.2f} {H:.2f}" role="img"{aria}><defs>{defs}</defs>'
            f'<g transform="scale({k:.5f})">{body}</g>' + inner + "</svg>")


def ref_height(svg):
    """Altura da peça embrulhada, em unidades de referência."""
    m = re.search(r'<svg\b[^>]*\bwidth="([\d.]+)"[^>]*\bheight="([\d.]+)"', svg)
    w, h = float(m.group(1)), float(m.group(2))
    return h * CARD / w + GAP


def write_panel(path, y0=None, lang="pt"):
    """Grava <nome>-panel.svg (pt) e <nome>-panel-en.svg (en) se a peça faz parte do README em imagens.

    No layout, as posições do README em inglês ficam com o prefixo "en/".
    """
    path = Path(path)
    if y0 is None:
        lay = layout()
        outs = [write_panel(path, lay[k], lg) for lg, k in (("pt", path.stem), ("en", "en/" + path.stem)) if k in lay]
        return outs[0] if outs else None
    out = path.with_name(path.stem + ("-panel.svg" if lang == "pt" else f"-panel-{lang}.svg"))
    out.write_text(wrap(path.read_text(encoding="utf-8"), path.stem, y0), encoding="utf-8")
    return out

if __name__ == "__main__":
    for p in sys.argv[1:]:
        print(f"wrote {write_panel(p)}")
