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
        '<radialGradient id="glow" cx="0.5" cy="1" r="0.6"><stop offset="0" stop-color="#58a6ff" stop-opacity="0.25"/><stop offset="1" stop-color="#58a6ff" stop-opacity="0"/></radialGradient>',
        '<clipPath id="frame"><rect x="1" y="1" width="958" height="338" rx="18"/></clipPath></defs>',
        '<g clip-path="url(#frame)">',
        f'<rect width="{W}" height="{H}" fill="url(#sky)"/>',
        f'<rect y="{ground - 160}" width="{W}" height="200" fill="url(#glow)"/>',
    ]
    for _ in range(70):  # estrelas piscando
        x, y, r, d = rnd() * W, rnd() * 170, 0.5 + rnd() * 1.1, 2 + rnd() * 4
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" fill="#f0f6fc"><animate attributeName="opacity" values="0.2;1;0.2" dur="{d:.1f}s" begin="{rnd() * 3:.1f}s" repeatCount="indefinite"/></circle>')
    out.append('<circle cx="560" cy="62" r="26" fill="#f0f6fc" opacity="0.9"/><circle cx="572" cy="54" r="24" fill="#05070d" opacity="0.85"/>')
    # cometa cruzando o céu
    out.append('<line x1="0" y1="0" x2="60" y2="18" stroke="#7ee787" stroke-width="2" stroke-linecap="round" opacity="0.8"><animateTransform attributeName="transform" type="translate" values="-80 30; 1040 160" dur="7s" repeatCount="indefinite"/></line>')
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
        f'<rect y="{ground + 14}" width="40" height="2" fill="#d29922" opacity="0.7"><animateTransform attributeName="transform" type="translate" values="-60 0; 1000 0" dur="5s" repeatCount="indefinite"/></rect>',
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
    for name, svg in (("stats.svg", stats_card(user)), ("languages.svg", langs_card(user)), ("city.svg", city_card(user))):
        ElementTree.fromstring(svg)  # self-check: SVG bem formado
        (OUT / name).write_text(svg, encoding="utf-8")
        print(f"wrote assets/{name}")


if __name__ == "__main__":
    main()
