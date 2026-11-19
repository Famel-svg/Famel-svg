"""Gera o hero e o cartão de stack do perfil (PT e EN). Visual: fundo escuro com brilhos e chips.

Uso: python scripts/build_brand.py
"""
from html import escape
from pathlib import Path
from xml.etree import ElementTree

from panel import write_panel

OUT = Path(__file__).resolve().parent.parent / "assets"
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,'SF Mono',Menlo,Consolas,monospace"
A1, A2, SOFT, INK = "#58a6ff", "#3fb950", "#9ecbff", "#e6f1ff"

TEXT = {
    "pt": {
        "role": "Backend Java · Spring Boot · Android",
        "tag": "APIs que aguentam concorrência, falha e auditoria.",
        "num_label": "PROJETOS PUBLICADOS",
        "num_sub": ["APIs, apps e dados", "com testes e CI"],
        "stack": [
            ("Linguagens", ["Java 21", "Kotlin", "SQL", "Python", "TypeScript", "Rust"]),
            ("Backend", ["Spring Boot", "Spring Security", "JPA/Hibernate", "JWT", "WebSocket"]),
            ("Dados e mensageria", ["PostgreSQL", "Flyway", "RabbitMQ", "Firestore", "Power BI"]),
            ("Qualidade e deploy", ["JUnit 5", "Testcontainers", "JaCoCo", "Docker", "GitHub Actions"]),
            ("Mobile e observabilidade", ["Jetpack Compose", "Room", "Prometheus", "Grafana"]),
        ],
    },
    "en": {
        "role": "Java Backend · Spring Boot · Android",
        "tag": "APIs built to survive concurrency, failure and audits.",
        "num_label": "PUBLISHED PROJECTS",
        "num_sub": ["APIs, apps and data", "with tests and CI"],
        "stack": [
            ("Languages", ["Java 21", "Kotlin", "SQL", "Python", "TypeScript", "Rust"]),
            ("Backend", ["Spring Boot", "Spring Security", "JPA/Hibernate", "JWT", "WebSocket"]),
            ("Data and messaging", ["PostgreSQL", "Flyway", "RabbitMQ", "Firestore", "Power BI"]),
            ("Quality and deploy", ["JUnit 5", "Testcontainers", "JaCoCo", "Docker", "GitHub Actions"]),
            ("Mobile and observability", ["Jetpack Compose", "Room", "Prometheus", "Grafana"]),
        ],
    },
}
PROJECTS = 15  # projetos listados na tabela do README


def text(x, y, s, size, fill, family=SANS, weight=400, anchor="start", opacity=1, spacing=0):
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
            f'fill-opacity="{opacity}" text-anchor="{anchor}" letter-spacing="{spacing}">{escape(s)}</text>')


def chip(x, y, label):
    w = 22 + 7.2 * len(label)
    return w, (f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="24" rx="12" fill="{A1}" fill-opacity="0.10" stroke="{SOFT}" stroke-opacity="0.6"/>'
               + text(f"{x + 11:.1f}", y + 16.5, label, 12, INK, MONO))


def frame(h, body):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="860" height="{h}" viewBox="0 0 860 {h}" role="img">
<defs>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#05070d"/><stop offset="0.55" stop-color="#0d1a33"/><stop offset="1" stop-color="#05070d"/></linearGradient>
<radialGradient id="o1"><stop offset="0" stop-color="{A1}" stop-opacity="0.5"/><stop offset="0.6" stop-color="{A1}" stop-opacity="0.1"/><stop offset="1" stop-color="{A1}" stop-opacity="0"/></radialGradient>
<radialGradient id="o2"><stop offset="0" stop-color="{A2}" stop-opacity="0.4"/><stop offset="0.6" stop-color="{A2}" stop-opacity="0.08"/><stop offset="1" stop-color="{A2}" stop-opacity="0"/></radialGradient>
<linearGradient id="line" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{A1}"/><stop offset="1" stop-color="{A2}"/></linearGradient>
<clipPath id="clip"><rect x="1" y="1" width="858" height="{h - 2}" rx="18"/></clipPath>
</defs>
<g clip-path="url(#clip)"><rect width="860" height="{h}" fill="url(#bg)"/>
<circle cx="100" cy="20" r="{h * 0.9:.0f}" fill="url(#o1)"/><circle cx="790" cy="{h - 10}" r="{h * 0.8:.0f}" fill="url(#o2)"/></g>
<rect x="1" y="1" width="858" height="{h - 2}" rx="18" fill="none" stroke="{A1}" stroke-opacity="0.5" stroke-width="1.5"/>
{body}
</svg>
"""


def hero(t):
    body = [
        f'<circle cx="104" cy="110" r="58" fill="none" stroke="url(#line)" stroke-width="3"/>',
        f'<circle cx="104" cy="110" r="50" fill="{A1}" fill-opacity="0.12"/>',
        text(104, 124, "RT", 38, INK, weight=700, anchor="middle"),
        text(196, 62, "@Famel-svg", 14, SOFT, MONO),
        text(194, 106, "Rafael Tanimoto", 42, INK, weight=800),
        text(196, 138, t["role"], 18, INK, weight=600, opacity=0.95),
        text(196, 162, t["tag"], 14, SOFT, opacity=0.9),
    ]
    x = 196
    for label in ["Java", "Spring Boot", "Kotlin", "PostgreSQL", "RabbitMQ", "Docker"]:
        w, svg = chip(x, 180, label)
        body.append(svg)
        x += w + 8
    body += [
        f'<line x1="700" y1="44" x2="700" y2="196" stroke="{SOFT}" stroke-opacity="0.25"/>',
        text(780, 104, str(PROJECTS), 58, A1, weight=800, anchor="middle"),
        text(780, 132, t["num_label"], 10.5, INK, MONO, 600, "middle", spacing=1),
        text(780, 156, t["num_sub"][0], 11.5, SOFT, anchor="middle", opacity=0.85),
        text(780, 172, t["num_sub"][1], 11.5, SOFT, anchor="middle", opacity=0.85),
    ]
    return frame(236, "\n".join(body))


def stack(t):
    body = [text(32, 44, "stack", 14, SOFT, MONO), f'<line x1="32" y1="60" x2="828" y2="60" stroke="url(#line)" stroke-opacity="0.7"/>']
    for i, (group, items) in enumerate(t["stack"]):
        y = 79 + i * 44
        body.append(text(32, y + 17, group, 13, SOFT, weight=600))
        x = 260
        for label in items:
            w, svg = chip(x, y, label)
            body.append(svg)
            x += w + 8
        assert x < 860, f"chips estouram a largura em {group}"
    return frame(79 + len(t["stack"]) * 44 + 16, "\n".join(body))


def main():
    for lang, t in TEXT.items():
        for name, svg in ((f"hero-{lang}.svg", hero(t)), (f"stack-{lang}.svg", stack(t))):
            ElementTree.fromstring(svg)  # self-check: SVG bem formado
            (OUT / name).write_text(svg, encoding="utf-8")
            print(f"wrote assets/{name}")
            if write_panel(OUT / name):
                print(f"wrote panel for {name}")


if __name__ == "__main__":
    main()
