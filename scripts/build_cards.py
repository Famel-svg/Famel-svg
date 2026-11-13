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
    contributionsCollection { totalCommitContributions contributionCalendar { totalContributions } }
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


def main():
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        raise SystemExit("Defina GITHUB_TOKEN ou GH_TOKEN.")
    user = fetch(token)
    OUT.mkdir(exist_ok=True)
    for name, svg in (("stats.svg", stats_card(user)), ("languages.svg", langs_card(user))):
        ElementTree.fromstring(svg)  # self-check: SVG bem formado
        (OUT / name).write_text(svg, encoding="utf-8")
        print(f"wrote assets/{name}")


if __name__ == "__main__":
    main()
