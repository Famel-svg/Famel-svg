"""Monta o README em imagens: cada peça vira um SVG com o fundo animado, empilhadas sem espaço.

Ordem do que acontece:
1. node scripts/build_readme_images.js  -> PNGs transparentes em assets/readme/src/
2. python scripts/build_readme.py       -> este script:
   - calcula onde cada peça começa na página (data/readme-layout.json);
   - embrulha cada PNG num SVG com a sua fatia do fundo (assets/readme/<nome>.svg);
   - refaz os *-panel.svg dos cartões dinâmicos (hero, cidade, stats, stack);
   - escreve o README.md, com a versão em texto (scripts/readme_text.py) no fim.

O fundo é desenhado em coordenadas de referência (página de 860 de largura), então a grade
fica alinhada e a varredura desce de uma imagem para a seguinte.
"""
import base64
import json
import struct
from pathlib import Path

from panel import LAYOUT, REF_W, background, ref_height, write_panel
from readme_text import markdown

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
SRC = ASSETS / "readme" / "src"

LI = "https://www.linkedin.com/in/rafaeltanimoto/"
MAIL = "mailto:rafaelandradetanimoto@gmail.com"
GH = "https://github.com/Famel-svg/"

# Cada linha é uma lista de peças lado a lado: (tipo, nome, alt, link, cantos arredondados)
# tipo "png" = assets/readme/src/<nome>.png; "svg" = assets/<nome>.svg (cartão dinâmico).
PROJECTS = [
    ("p-safepix", "SafePix_Async", "SafePix Async"),
    ("p-auditoria", "Sistema_Auditoria_PIX", "Auditoria PIX"),
    ("p-estoque", "estoque-reserva", "Estoque Reserva"),
    ("p-salas", "reserva-salas", "Reserva de Salas"),
    ("p-biblioteca", "biblioteca-emprestimos", "Biblioteca Empréstimos"),
    ("p-auth", "auth-rbac-starter", "Auth RBAC Starter"),
    ("p-financeiro", "Sistema_De_Controle_Financeiro", "Controle Financeiro"),
    ("p-store", "springboot_simple_store", "Simple Store"),
    ("p-wtc", "WTC_Chat", "WTC CRM Chat"),
    ("p-fluxo", "fluxo-android", "Fluxo"),
    ("p-repforge", "repforge", "RepForge"),
    ("p-apk", "apk-preview-desktop", "APK Preview Desktop"),
    ("p-brave", "Brave_CLI", "Brave CLI"),
    ("p-combustiveis", "combustiveis-sql-analytics", "Combustíveis SQL Analytics"),
    ("p-powerbi", "painel-combustiveis-powerbi", "Painel Power BI"),
]
proj = [("png", s, n, GH + r, "") for s, r, n in PROJECTS] + [("png", "p-empty", "", None, "")]

ROWS = [
    [("png", "top-pt", "Português (atual)", None, "tl"), ("png", "top-en", "English", "versions/README-en.md", "tr")],
    [("svg", "hero-pt", "Rafael Tanimoto — backend Java, Spring Boot e Android", None, "")],
    [("png", "chips", "Aberto a oportunidades · São Paulo, remoto ou híbrido · inglês fluente", None, "")],
    [("png", "social-li", "LinkedIn", LI, ""), ("png", "social-mail", "Email", MAIL, "")],
    [("svg", "city", "Cidade animada das minhas contribuições no GitHub", None, "")],
    [("png", "about", "01 / Sobre: backend Java e Spring Boot, apps Android em Kotlin. Procuro vaga júnior em backend Java ou Android, remota ou híbrida.", None, "")],
    [("svg", "overview", "Estatísticas do GitHub e linguagens mais usadas", None, "")],
    [("png", "cases-title", "02 / Estudos de caso", None, "")],
    [("png", "case-1", "Estudo de caso 1: Pagamento que não duplica — SafePix Async", GH + "SafePix_Async", ""),
     ("png", "case-2", "Estudo de caso 2: Quem mexeu nisso? — Auditoria PIX", GH + "Sistema_Auditoria_PIX", ""),
     ("png", "case-3", "Estudo de caso 3: O último item do estoque — Estoque Reserva", GH + "estoque-reserva", "")],
    [("png", "projects-title", "03 / Todos os projetos", None, "")],
    *[proj[i:i + 2] for i in range(0, len(proj), 2)],
    [("svg", "stack-pt", "04 / Stack: Java 21, Kotlin, SQL, Python, Spring Boot, Spring Security, JPA, PostgreSQL, Flyway, RabbitMQ, JUnit 5, Testcontainers, Docker, GitHub Actions, Jetpack Compose, Prometheus, Grafana", None, "")],
    [("png", "education", "05 / Formação: FIAP (2026), Anhembi Morumbi (não concluído), qualificações FIAP", None, "")],
    [("png", "contact", "06 / Contato: me chame no LinkedIn ou por email", None, "b")],
]


def png_size(path):
    w, h = struct.unpack(">II", path.read_bytes()[16:24])
    return w / 2, h / 2  # renderizado com deviceScaleFactor 2


def clip(w, h, corners, r=20):
    tl = r if "tl" in corners else 0
    tr = r if "tr" in corners else 0
    bl = br = r if "b" in corners else 0
    return (f'<clipPath id="round"><path d="M{tl},0 H{w - tr} Q{w},0 {w},{tr} V{h - br} Q{w},{h} {w - br},{h} '
            f'H{bl} Q0,{h} 0,{h - bl} V{tl} Q0,0 {tl},0 Z"/></clipPath>')


def encode(png):
    """WebP com transparência: ~80 KB por peça em vez de ~1 MB do PNG."""
    import io
    from PIL import Image  # pip install pillow
    buf = io.BytesIO()
    Image.open(png).save(buf, "WEBP", quality=90, method=6)
    return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()


def png_piece(name, x0, y0, corners):
    png = SRC / f"{name}.png"
    w, h = png_size(png)
    defs, body = background(w, h, x0, y0, name)
    data = encode(png)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" '
           f'width="{w:g}" height="{h:g}" viewBox="0 0 {w:g} {h:g}" role="img">'
           f'<defs>{defs}{clip(w, h, corners)}</defs><g clip-path="url(#round)">{body}'
           f'<image width="{w:g}" height="{h:g}" href="{data}"/></g></svg>')
    (ASSETS / "readme" / f"{name}.svg").write_text(svg, encoding="utf-8")
    return w


def main():
    # 1. alturas e posições
    y, offsets, rows = 0.0, {}, []
    for row in ROWS:
        x, h, cells = 0.0, 0.0, []
        for kind, name, alt, href, corners in row:
            if kind == "png":
                w, ph = png_size(SRC / f"{name}.png")
            else:
                w, ph = REF_W, ref_height((ASSETS / f"{name}.svg").read_text(encoding="utf-8"))
            offsets[name] = round(y, 2)
            cells.append((kind, name, alt, href, corners, x, w))
            x, h = x + w, max(h, ph)
        assert abs(x - REF_W) < 0.5, f"linha com largura {x}: {[c[1] for c in row]}"
        rows.append(cells)
        y += h
    LAYOUT.write_text(json.dumps(offsets, indent=1) + "\n", encoding="utf-8")

    # 2. peças
    html = []
    for cells in rows:
        for kind, name, alt, href, corners, x0, w in cells:
            if kind == "png":
                png_piece(name, x0, offsets[name], corners)
                src = f"./assets/readme/{name}.svg"
            else:
                write_panel(ASSETS / f"{name}.svg", offsets[name])
                src = f"./assets/{name}-panel.svg"
            img = f'<img src="{src}" alt="{alt}" width="{w / REF_W * 100:.3f}%" align="top" />'
            html.append(f'<a href="{href}">{img}</a>' if href else img)

    # 3. README
    (ROOT / "README.md").write_text(
        "<!-- README em imagens, gerado por scripts/build_readme.py (não edite à mão).\n"
        "     Cada peça traz sua fatia do fundo animado e fica empilhada sem espaço (align=\"top\"). -->\n"
        "<p>" + "".join(html) + "</p>\n"
        + markdown([(sh, GH + repo) for sh, repo, _ in PROJECTS],
                   {"case-1": GH + "SafePix_Async", "case-2": GH + "Sistema_Auditoria_PIX", "case-3": GH + "estoque-reserva"},
                   LI, MAIL),
        encoding="utf-8")
    print(f"wrote README.md, {sum(len(r) for r in rows)} peças, altura {y:.0f}")


if __name__ == "__main__":
    main()
