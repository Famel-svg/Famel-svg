"""Embrulha um SVG do perfil num "painel" escuro com estrelas, para o README em imagens.

As peças do README ficam empilhadas sem espaço entre si; cada uma traz o mesmo fundo
(PANEL) nas margens, então o conjunto parece um único plano de fundo contínuo.
As proporções batem com scripts/readme-sections.html: cartão de 812 px numa faixa de 860 px.

Uso: python scripts/panel.py assets/city.svg [...]  -> grava assets/city-panel.svg
"""
import random
import re
import sys
from pathlib import Path

PANEL = "#05070d"
SLICE, CARD, GAP = 860, 812, 16  # mesma geometria das imagens PNG


def stars(rnd, w, h, boxes, n):
    """Pontinhos aleatórios só nas margens (fora do cartão)."""
    out = []
    while len(out) < n:
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        if any(x0 <= x <= x1 and y0 <= y <= y1 for x0, y0, x1, y1 in boxes):
            continue
        r = rnd.uniform(0.5, 1.2) * w / SLICE
        col = rnd.choice(("#9ecbff", "#e6f1ff", "#58a6ff", "#3fb950"))
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.2f}" fill="{col}" opacity="{rnd.uniform(0.25, 0.7):.2f}"/>')
    return "".join(out)


def wrap(svg, seed):
    m = re.search(r'<svg\b[^>]*\bwidth="([\d.]+)"[^>]*\bheight="([\d.]+)"', svg)
    w, h = float(m.group(1)), float(m.group(2))
    k = w / CARD
    mx, gap = (SLICE - CARD) / 2 * k, GAP * k
    W, H = w + 2 * mx, h + gap
    rnd = random.Random(seed)
    label = re.search(r'aria-label="([^"]*)"', svg)
    aria = f' aria-label="{label.group(1)}"' if label else ""
    inner = re.sub(r"^<svg\b", f'<svg x="{mx:.2f}" y="0"', svg.strip(), count=1)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.2f}" height="{H:.2f}" '
            f'viewBox="0 0 {W:.2f} {H:.2f}" role="img"{aria}>'
            f'<rect width="100%" height="100%" fill="{PANEL}"/>'
            + stars(rnd, W, H, [(mx, 0, mx + w, h)], int(H / 12))
            + inner + "</svg>")


def write_panel(path):
    path = Path(path)
    out = path.with_name(path.stem + "-panel.svg")
    out.write_text(wrap(path.read_text(encoding="utf-8"), path.stem), encoding="utf-8")
    return out


if __name__ == "__main__":
    for p in sys.argv[1:]:
        print(f"wrote {write_panel(p)}")
