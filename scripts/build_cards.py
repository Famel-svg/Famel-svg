"""Gera os cartões SVG do perfil (estatísticas e linguagens) a partir da API GraphQL do GitHub.

Substitui o github-readme-stats público. Uso: GITHUB_TOKEN=... python scripts/build_cards.py
"""
import json
import os
import urllib.request
from html import escape
from pathlib import Path
from xml.etree import ElementTree

USER = os.environ.get("GH_USER", "Famel-svg")
OUT = Path(__file__).resolve().parent.parent / "assets"
FONT = "Consolas,monospace"
BG, BORDER, MUTED, TEXT, GREEN, BLUE = "#0d1117", "#30363d", "#8b949e", "#f0f6fc", "#7ee787", "#58a6ff"
IGNORED_LANGS = {"HTML", "CSS", "Jupyter Notebook", "Wolfram Language", "Batchfile", "Shell", "PowerShell"}

QUERY = """
query($login: String!) {
  user(login: $login) {
    repositories(ownerAffiliations: OWNER, isFork: false, first: 100, privacy: PUBLIC) {
      totalCount
      nodes {
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name color } } }
      }
    }
    pullRequests { totalCount }
    contributionsCollection {
      totalCommitContributions
      contributionCalendar { totalContributions weeks { contributionDays { contributionCount date } } }
    }
  }
}
"""


def fetch(token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.load(resp)
    if "errors" in body:
        raise SystemExit(f"GraphQL error: {body['errors']}")
    return body["data"]["user"]


def frame(width, height, title, body):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">
  <rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="14" fill="{BG}" stroke="{BORDER}" stroke-width="2"/>
  <circle cx="24" cy="24" r="5" fill="#ff7b72"/><circle cx="42" cy="24" r="5" fill="#d29922"/><circle cx="60" cy="24" r="5" fill="#3fb950"/>
  <text x="80" y="29" fill="{MUTED}" font-family="{FONT}" font-size="14">{escape(title)}</text>
  <path d="M1 46h{width - 2}" stroke="{BORDER}" stroke-width="2"/>
{body}
</svg>
"""


def stats_card(user):
    repos = user["repositories"]
    rows = [
        ("Contribuições no último ano", user["contributionsCollection"]["contributionCalendar"]["totalContributions"]),
        ("Commits no último ano", user["contributionsCollection"]["totalCommitContributions"]),
        ("Repositórios públicos", repos["totalCount"]),
        ("Pull requests", user["pullRequests"]["totalCount"]),
        ("Estrelas recebidas", sum(r["stargazerCount"] for r in repos["nodes"])),
    ]
    body = [f'  <text x="28" y="78" fill="{GREEN}" font-family="{FONT}" font-size="15">$ git stats --author rafael</text>']
    for i, (label, value) in enumerate(rows):
        y = 112 + i * 28
        body.append(f'  <text x="28" y="{y}" fill="{MUTED}" font-family="{FONT}" font-size="15">{escape(label)}</text>')
        body.append(f'  <text x="440" y="{y}" fill="{TEXT}" font-family="{FONT}" font-size="15" font-weight="700" text-anchor="end">{value}</text>')
    return frame(470, 112 + len(rows) * 28, "stats", "\n".join(body))


def langs_card(user, top=6):
    totals, colors = {}, {}
    for repo in user["repositories"]["nodes"]:
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            if name in IGNORED_LANGS:
                continue
            totals[name] = totals.get(name, 0) + edge["size"]
            colors[name] = edge["node"]["color"] or BLUE
    ranked = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)[:top]
    total = sum(size for _, size in ranked) or 1
    body = [f'  <text x="28" y="78" fill="{GREEN}" font-family="{FONT}" font-size="15">$ linguist --top {top}</text>']
    bar_x, bar_w, x = 28, 414, 28.0
    for name, size in ranked:
        w = bar_w * size / total
        body.append(f'  <rect x="{x:.1f}" y="94" width="{w:.1f}" height="10" fill="{colors[name]}"/>')
        x += w
    for i, (name, size) in enumerate(ranked):
        col, row = i % 2, i // 2
        cx, cy = 34 + col * 214, 134 + row * 28
        body.append(f'  <circle cx="{cx}" cy="{cy - 5}" r="5" fill="{colors[name]}"/>')
        body.append(f'  <text x="{cx + 14}" y="{cy}" fill="{TEXT}" font-family="{FONT}" font-size="15">{escape(name)} <tspan fill="{MUTED}">{100 * size / total:.1f}%</tspan></text>')
    height = 134 + ((len(ranked) + 1) // 2) * 28 - 6
    return frame(470, max(height, 112 + 5 * 28), "linguagens", "\n".join(body))


def city_card(user):
    """Cidade noturna animada: um prédio por semana, altura pelas contribuições."""
    cal = user["contributionsCollection"]["contributionCalendar"]
    weeks = [sum(d["contributionCount"] for d in w["contributionDays"]) for w in cal["weeks"]]
    W, H, ground = 960, 340, 300
    peak = max(weeks) or 1
    bw, gap = 14, 3.6
    x0 = (W - len(weeks) * (bw + gap)) / 2
    seed = 7

    def rnd():
        nonlocal seed
        seed = (seed * 1103515245 + 12345) % 2**31
        return seed / 2**31

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Cidade de contribuições: {cal["totalContributions"]} no último ano">',
        '<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#05070d"/><stop offset="0.7" stop-color="#0d1530"/><stop offset="1" stop-color="#1b1f4a"/></linearGradient>',
        '<radialGradient id="moonglow"><stop offset="0.45" stop-color="#f0f6fc" stop-opacity="0.35"/><stop offset="1" stop-color="#f0f6fc" stop-opacity="0"/></radialGradient><radialGradient id="glow" cx="0.5" cy="1" r="0.6"><stop offset="0" stop-color="#58a6ff" stop-opacity="0.25"/><stop offset="1" stop-color="#58a6ff" stop-opacity="0"/></radialGradient>',
        '<clipPath id="frame"><rect x="1" y="1" width="958" height="338" rx="18"/></clipPath></defs>',
        '<g clip-path="url(#frame)">',
        f'<rect width="{W}" height="{H}" fill="url(#sky)"/>',
        f'<rect y="{ground - 160}" width="{W}" height="200" fill="url(#glow)"/>',
        # ciclo dia/noite de 30s: céu claro aparece, sol cruza, noite volta
        '<linearGradient id="day" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3b82c4"/><stop offset="1" stop-color="#f2b880"/></linearGradient>',
        f'<rect width="{W}" height="{H}" fill="url(#day)" opacity="0"><animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;0.08;0.42;0.5;1" dur="60s" repeatCount="indefinite"/></rect>',
        '<circle r="22" fill="#ffd166"><animateTransform attributeName="transform" type="translate" values="-60 220;120 80;840 80;1020 220;1020 220" keyTimes="0;0.08;0.42;0.5;1" dur="60s" repeatCount="indefinite"/></circle>',
        '<g fill="#ffffff" opacity="0"><animate attributeName="opacity" values="0;0.9;0.9;0;0" keyTimes="0;0.08;0.42;0.5;1" dur="60s" repeatCount="indefinite"/>',
        '<g transform="translate(240 70) scale(1)"><g><animateTransform attributeName="transform" type="translate" values="0 0;-260 0;0 0" dur="90s" repeatCount="indefinite"/><ellipse cx="0" cy="0" rx="34" ry="12"/><ellipse cx="-14" cy="-8" rx="16" ry="12"/><ellipse cx="10" cy="-12" rx="20" ry="15"/></g></g>',
        '<g transform="translate(520 120) scale(0.8)"><g><animateTransform attributeName="transform" type="translate" values="0 0;-325 0;0 0" dur="120s" repeatCount="indefinite"/><ellipse cx="0" cy="0" rx="34" ry="12"/><ellipse cx="-14" cy="-8" rx="16" ry="12"/><ellipse cx="10" cy="-12" rx="20" ry="15"/></g></g>',
        '<g transform="translate(760 60) scale(1.2)"><g><animateTransform attributeName="transform" type="translate" values="0 0;-216 0;0 0" dur="100s" repeatCount="indefinite"/><ellipse cx="0" cy="0" rx="34" ry="12"/><ellipse cx="-14" cy="-8" rx="16" ry="12"/><ellipse cx="10" cy="-12" rx="20" ry="15"/></g></g>',
        '<g transform="translate(900 140) scale(0.7)"><g><animateTransform attributeName="transform" type="translate" values="0 0;-371 0;0 0" dur="140s" repeatCount="indefinite"/><ellipse cx="0" cy="0" rx="34" ry="12"/><ellipse cx="-14" cy="-8" rx="16" ry="12"/><ellipse cx="10" cy="-12" rx="20" ry="15"/></g></g>',
        '<g transform="translate(120 150) scale(0.9)"><g><animateTransform attributeName="transform" type="translate" values="0 0;-288 0;0 0" dur="110s" repeatCount="indefinite"/><ellipse cx="0" cy="0" rx="34" ry="12"/><ellipse cx="-14" cy="-8" rx="16" ry="12"/><ellipse cx="10" cy="-12" rx="20" ry="15"/></g></g>',
        '</g>',
    ]
    # avião com luzes piscando
    out.append('<g><animateTransform attributeName="transform" type="translate" values="1000 70;1000 70;-80 50;-80 50" keyTimes="0;0.1;0.36;1" dur="60s" repeatCount="indefinite"/>'
               '<path d="M0 0 L22 0 L26 -2 L22 -4 L4 -4 Z M10 -3 L16 -11 L19 -11 L15 -3 Z M10 -1 L16 5 L19 5 L15 -1 Z" fill="#8b949e"/>'
               '<circle cx="0" cy="-2" r="1.6" fill="#ff7b72"><animate attributeName="opacity" values="1;0;1" dur="1s" repeatCount="indefinite"/></circle>'
               '<circle cx="26" cy="-2" r="1.6" fill="#f0f6fc"><animate attributeName="opacity" values="0;1;0" dur="1s" repeatCount="indefinite"/></circle></g>')
    out.append('<g opacity="1"><animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;0.5;0.58;0.92;1" dur="60s" repeatCount="indefinite"/>')  # grupo noturno
    for _ in range(70):  # estrelas piscando
        x, y, r, d = rnd() * W, rnd() * 170, 0.5 + rnd() * 1.1, 2 + rnd() * 4
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" fill="#f0f6fc"><animate attributeName="opacity" values="0.2;1;0.2" dur="{d:.1f}s" begin="{rnd() * 3:.1f}s" repeatCount="indefinite"/></circle>')
    out.append('<g><animateTransform attributeName="transform" type="translate" values="-60 220;-60 220;120 80;840 80;1020 220" keyTimes="0;0.5;0.58;0.92;1" dur="60s" repeatCount="indefinite"/><circle r="44" fill="url(#moonglow)"/><circle r="22" fill="#e8e4d4"/><circle cx="-7" cy="-6" r="5" fill="#cfc9b4"/><circle cx="8" cy="4" r="3.5" fill="#cfc9b4"/><circle cx="-3" cy="10" r="2.5" fill="#cfc9b4"/><circle cx="10" cy="-9" r="2" fill="#cfc9b4"/></g>')
    # óvni: entra, para sobre a cidade com feixe de luz e sai
    out.append('<g><animateTransform attributeName="transform" type="translate" values="-60 110;-60 110;420 110;440 104;460 110;1020 90;1020 90" keyTimes="0;0.6;0.68;0.74;0.8;0.88;1" dur="60s" repeatCount="indefinite"/>'
               '<polygon points="-6,6 6,6 22,90 -22,90" fill="#7ee787" opacity="0"><animate attributeName="opacity" values="0;0;0.25;0.25;0;0" keyTimes="0;0.68;0.7;0.78;0.8;1" dur="60s" repeatCount="indefinite"/></polygon>'
               '<ellipse cx="0" cy="0" rx="9" ry="7" fill="#58a6ff" opacity="0.7"/><ellipse cx="0" cy="4" rx="22" ry="5" fill="#8b949e"/>'
               '<circle cx="-12" cy="5" r="1.5" fill="#7ee787"><animate attributeName="fill" values="#7ee787;#d29922;#ff7b72;#7ee787" dur="1.2s" repeatCount="indefinite"/></circle>'
               '<circle cx="0" cy="6" r="1.5" fill="#d29922"><animate attributeName="fill" values="#d29922;#ff7b72;#7ee787;#d29922" dur="1.2s" repeatCount="indefinite"/></circle>'
               '<circle cx="12" cy="5" r="1.5" fill="#ff7b72"><animate attributeName="fill" values="#ff7b72;#7ee787;#d29922;#ff7b72" dur="1.2s" repeatCount="indefinite"/></circle></g>')
    out.append('</g>')
    for i, total in enumerate(weeks):
        h = 8 + (ground - 90) * (total / peak) ** 0.6
        x, y = x0 + i * (bw + gap), ground - h
        delay = i * 0.03
        tone = "#161b22" if total == 0 else ("#1f2a44" if total < peak * 0.4 else "#22305a")
        out.append(f'<g><rect x="{x:.1f}" y="{y:.1f}" width="{bw}" height="{h:.1f}" fill="{tone}" stroke="#30363d" stroke-width="0.6">'
                   f'<animate attributeName="height" from="0" to="{h:.1f}" dur="1.2s" begin="{delay:.2f}s" fill="freeze"/>'
                   f'<animate attributeName="y" from="{ground}" to="{y:.1f}" dur="1.2s" begin="{delay:.2f}s" fill="freeze"/></rect>')
        out.append(f'<polygon points="{x + bw:.1f},{y:.1f} {x + bw + gap:.1f},{y + 3:.1f} {x + bw + gap:.1f},{ground} {x + bw:.1f},{ground}" fill="#0b0f1c" opacity="0"><animate attributeName="opacity" to="1" dur="0.3s" begin="{delay + 1.1:.2f}s" fill="freeze"/></polygon>')
        for wy in range(int(y) + 6, ground - 6, 9):  # janelas
            for wx in (x + 3, x + 8.5):
                if rnd() < 0.45 * (total > 0):
                    color = "#d29922" if rnd() < 0.8 else "#58a6ff"
                    out.append(f'<rect x="{wx:.1f}" y="{wy}" width="2.6" height="3.4" fill="{color}" opacity="0"><animate attributeName="opacity" values="0;1;1;0.35;1" keyTimes="0;0.1;0.6;0.7;1" dur="{4 + rnd() * 6:.1f}s" begin="{delay + 1.2:.2f}s" repeatCount="indefinite"/></rect>')
        if total == peak:
            out.append(f'<circle cx="{x + bw / 2:.1f}" cy="{y - 6:.1f}" r="2.5" fill="#ff7b72"><animate attributeName="opacity" values="1;0.1;1" dur="1.4s" repeatCount="indefinite"/></circle>')
        out.append("</g>")
    out += [
        f'<rect y="{ground}" width="{W}" height="{H - ground}" fill="#0a0d16"/>',
        f'<line x1="0" y1="{ground}" x2="{W}" y2="{ground}" stroke="#58a6ff" stroke-opacity="0.5"/>',
        f'<text x="28" y="40" fill="{GREEN}" font-family="{FONT}" font-size="16">$ ./cidade --ano</text>',
        f'<text x="28" y="{ground + 28}" fill="{MUTED}" font-family="{FONT}" font-size="13">cada prédio é uma semana · {cal["totalContributions"]} contribuições no último ano</text>',
        "</g>",
        f'<rect x="1" y="1" width="958" height="338" rx="18" fill="none" stroke="{BORDER}" stroke-width="2"/>',
        "</svg>",
    ]
    return "\n".join(out)


def main():
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        raise SystemExit("Defina GITHUB_TOKEN ou GH_TOKEN.")
    user = fetch(token)
    OUT.mkdir(exist_ok=True)
    stats, langs = stats_card(user), langs_card(user)
    # cartões lado a lado num único SVG: o GitHub empilha duas <img> em telas estreitas
    pair = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="960" height="252" viewBox="0 0 960 252" role="img" aria-label="Estatísticas e linguagens">'
        + stats.replace("<svg ", '<svg x="0" ', 1) + langs.replace("<svg ", '<svg x="490" ', 1) + "</svg>"
    )
    for name, svg in (("stats.svg", stats), ("languages.svg", langs), ("overview.svg", pair), ("city.svg", city_card(user))):
        ElementTree.fromstring(svg)  # self-check: SVG bem formado
        (OUT / name).write_text(svg, encoding="utf-8")
        print(f"wrote assets/{name}")


if __name__ == "__main__":
    main()
