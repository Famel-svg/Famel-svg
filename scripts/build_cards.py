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
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
SOFT, INK, A2 = "#9ecbff", "#e6f1ff", "#3fb950"  # mesmas cores de build_brand.py
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
    """Mesmo visual do hero e do stack: fundo em degradê, dois brilhos e borda azul."""
    k = escape(title)  # prefixo dos ids: overview.svg junta dois cartões no mesmo documento
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{k}">
  <defs>
    <linearGradient id="{k}-bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#05070d"/><stop offset="0.55" stop-color="#0d1a33"/><stop offset="1" stop-color="#05070d"/></linearGradient>
    <radialGradient id="{k}-o1"><stop offset="0" stop-color="{BLUE}" stop-opacity="0.45"/><stop offset="0.6" stop-color="{BLUE}" stop-opacity="0.1"/><stop offset="1" stop-color="{BLUE}" stop-opacity="0"/></radialGradient>
    <radialGradient id="{k}-o2"><stop offset="0" stop-color="{A2}" stop-opacity="0.35"/><stop offset="0.6" stop-color="{A2}" stop-opacity="0.08"/><stop offset="1" stop-color="{A2}" stop-opacity="0"/></radialGradient>
    <linearGradient id="{k}-line" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{BLUE}"/><stop offset="1" stop-color="{A2}"/></linearGradient>
    <clipPath id="{k}-clip"><rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="18"/></clipPath>
  </defs>
  <g clip-path="url(#{k}-clip)"><rect width="{width}" height="{height}" fill="url(#{k}-bg)"/>
    <circle cx="60" cy="10" r="{height * 0.9:.0f}" fill="url(#{k}-o1)"/><circle cx="{width - 40}" cy="{height - 10}" r="{height * 0.8:.0f}" fill="url(#{k}-o2)"/></g>
  <rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="18" fill="none" stroke="{BLUE}" stroke-opacity="0.5" stroke-width="1.5"/>
  <text x="28" y="34" fill="{SOFT}" font-family="{FONT}" font-size="14">{k}</text>
  <line x1="28" y1="48" x2="{width - 28}" y2="48" stroke="url(#{k}-line)" stroke-opacity="0.7"/>
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
    body = [f'  <text x="28" y="78" fill="{BLUE}" font-family="{FONT}" font-size="15">$ git stats --author rafael</text>']
    for i, (label, value) in enumerate(rows):
        y = 112 + i * 28
        body.append(f'  <text x="28" y="{y}" fill="{SOFT}" font-family="{SANS}" font-size="15">{escape(label)}</text>')
        body.append(f'  <text x="440" y="{y}" fill="{INK}" font-family="{FONT}" font-size="15" font-weight="700" text-anchor="end">{value}</text>')
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
    body = [f'  <text x="28" y="78" fill="{BLUE}" font-family="{FONT}" font-size="15">$ linguist --top {top}</text>']
    bar_x, bar_w, x = 28, 414, 28.0
    for name, size in ranked:
        w = bar_w * size / total
        body.append(f'  <rect x="{x:.1f}" y="94" width="{w:.1f}" height="10" fill="{colors[name]}"/>')
        x += w
    for i, (name, size) in enumerate(ranked):
        col, row = i % 2, i // 2
        cx, cy = 34 + col * 214, 134 + row * 28
        body.append(f'  <circle cx="{cx}" cy="{cy - 5}" r="5" fill="{colors[name]}"/>')
        body.append(f'  <text x="{cx + 14}" y="{cy}" fill="{INK}" font-family="{FONT}" font-size="15">{escape(name)} <tspan fill="{SOFT}">{100 * size / total:.1f}%</tspan></text>')
    height = 134 + ((len(ranked) + 1) // 2) * 28 - 6
    return frame(470, max(height, 112 + 5 * 28), "linguagens", "\n".join(body))


def city_card(user):
    """Cidade animada: um prédio por semana, altura pelas contribuições, ciclo de dia e noite de 60s."""
    cal = user["contributionsCollection"]["contributionCalendar"]
    weeks = [sum(d["contributionCount"] for d in w["contributionDays"]) for w in cal["weeks"]]
    W, H, ground = 960, 340, 262
    peak = max(weeks) or 1
    bw, gap = 14, 3.6
    x0 = (W - len(weeks) * (bw + gap)) / 2
    seed = 7

    def rnd():
        nonlocal seed
        seed = (seed * 1103515245 + 12345) % 2**31
        return seed / 2**31

    loop = 'dur="60s" repeatCount="indefinite"'
    # metade dia (0-0.5), metade noite (0.5-1); transições de 0.08
    day_on = f'values="0;1;1;0;0" keyTimes="0;0.08;0.42;0.5;1" {loop}'
    night_on = f'values="0;0;1;1;0" keyTimes="0;0.5;0.58;0.92;1" {loop}'
    dusk = f'values="0.8;0;0;0.8;0;0;0.8" keyTimes="0;0.08;0.42;0.5;0.58;0.92;1" {loop}'
    arc = "-70 230;90 150;260 108;480 92;700 108;870 150;1030 230"

    def arc_motion(start):
        # mesma trajetória para o sol (start=0) e para a lua (start=0.5)
        kt = ";".join(f"{start + k * 0.5 / 6:.3f}" for k in range(7))
        if start:
            return f'values="-70 230;{arc}" keyTimes="0;{kt}" {loop}'
        return f'values="{arc};1030 230" keyTimes="{kt};1" {loop}'

    def cloud(cx, cy, k, dur, begin):
        puffs = [(0, 0, 38, 13), (-20, -8, 18, 14), (6, -15, 22, 17), (26, -6, 16, 11)]
        body = "".join(f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}"/>' for x, y, rx, ry in puffs)
        return (f'<g transform="translate({cx} {cy}) scale({k})"><g>'
                f'<animateTransform attributeName="transform" type="translate" values="{(W - cx + 80) / k:.0f} 0;{(-cx - 120) / k:.0f} 0" dur="{dur}s" begin="-{begin}s" repeatCount="indefinite"/>'
                f'<g fill="#b9c7da" transform="translate(4 6)" opacity="0.6">{body}</g><g fill="url(#cloud)">{body}</g></g></g>')

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Cidade de contribuições: {cal["totalContributions"]} no último ano">',
        "<defs>",
        '<linearGradient id="night" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#05070d"/><stop offset="0.55" stop-color="#0d1a33"/><stop offset="1" stop-color="#05070d"/></linearGradient><radialGradient id="o1"><stop offset="0" stop-color="#58a6ff" stop-opacity="0.45"/><stop offset="0.6" stop-color="#58a6ff" stop-opacity="0.1"/><stop offset="1" stop-color="#58a6ff" stop-opacity="0"/></radialGradient><radialGradient id="o2"><stop offset="0" stop-color="#3fb950" stop-opacity="0.35"/><stop offset="0.6" stop-color="#3fb950" stop-opacity="0.08"/><stop offset="1" stop-color="#3fb950" stop-opacity="0"/></radialGradient><linearGradient id="line" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#58a6ff"/><stop offset="1" stop-color="#3fb950"/></linearGradient>',
        '<linearGradient id="day" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2f7fd1"/><stop offset="0.65" stop-color="#8cc4ee"/><stop offset="1" stop-color="#f6d7a7"/></linearGradient>',
        '<linearGradient id="dusk" x1="0" y1="0" x2="0" y2="1"><stop offset="0.35" stop-color="#ff8c42" stop-opacity="0"/><stop offset="1" stop-color="#ff6b3d" stop-opacity="0.85"/></linearGradient>',
        '<radialGradient id="sunhalo"><stop offset="0.3" stop-color="#ffe29a" stop-opacity="0.7"/><stop offset="1" stop-color="#ffe29a" stop-opacity="0"/></radialGradient>',
        '<linearGradient id="retro" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffe08a"/><stop offset="1" stop-color="#ff7a45"/></linearGradient>',
        '<clipPath id="stripes"><rect x="-30" y="-30" width="60" height="31"/><rect x="-30" y="4" width="60" height="5"/><rect x="-30" y="12" width="60" height="4"/><rect x="-30" y="19" width="60" height="3"/><rect x="-30" y="25" width="60" height="5"/></clipPath>',
        '<radialGradient id="moonglow"><stop offset="0.4" stop-color="#dfe9ff" stop-opacity="0.4"/><stop offset="1" stop-color="#dfe9ff" stop-opacity="0"/></radialGradient>',
        '<radialGradient id="moon" cx="0.35" cy="0.35"><stop offset="0" stop-color="#fbfaf2"/><stop offset="1" stop-color="#cfcab6"/></radialGradient>',
        '<linearGradient id="cloud" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffffff"/><stop offset="1" stop-color="#e3ebf5"/></linearGradient>',
        '<linearGradient id="bld" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#34466f"/><stop offset="1" stop-color="#141b30"/></linearGradient>',
        '<linearGradient id="bldhot" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3f5a92"/><stop offset="1" stop-color="#18213d"/></linearGradient>',
        '<linearGradient id="far" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2a3557"/><stop offset="1" stop-color="#1a2240"/></linearGradient>',
        '<linearGradient id="trail" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#ffffff" stop-opacity="0.8"/><stop offset="1" stop-color="#ffffff" stop-opacity="0"/></linearGradient>',
        '<radialGradient id="lamp"><stop offset="0" stop-color="#ffd27a" stop-opacity="0.8"/><stop offset="1" stop-color="#ffd27a" stop-opacity="0"/></radialGradient>',
        '<linearGradient id="beam" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#7ee787" stop-opacity="0.5"/><stop offset="1" stop-color="#7ee787" stop-opacity="0"/></linearGradient>',
        f'<clipPath id="frame"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="18"/></clipPath>',
        "</defs>",
        '<g clip-path="url(#frame)">',
        f'<rect width="{W}" height="{H}" fill="url(#night)"/>',
        f'<circle cx="100" cy="20" r="300" fill="url(#o1)"/><circle cx="{W - 70}" cy="{H - 10}" r="270" fill="url(#o2)"/>',
        f'<rect width="{W}" height="{H}" fill="url(#day)" opacity="0"><animate attributeName="opacity" {day_on}/></rect>',
        f'<rect width="{W}" height="{H}" fill="url(#dusk)" opacity="0"><animate attributeName="opacity" {dusk}/></rect>',
    ]

    # noite: estrelas, estrela cadente, lua, óvni
    out.append(f'<g opacity="0"><animate attributeName="opacity" {night_on}/>')
    for _ in range(90):
        x, y, r, d = rnd() * W, 62 + rnd() * 140, 0.4 + rnd() * 1.2, 2 + rnd() * 4
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" fill="#f0f6fc"><animate attributeName="opacity" values="0.2;1;0.2" dur="{d:.1f}s" begin="{rnd() * 3:.1f}s" repeatCount="indefinite"/></circle>')
    out.append(f'<line x1="0" y1="0" x2="70" y2="22" stroke="url(#trail)" stroke-width="1.6" stroke-linecap="round" opacity="0">'
               f'<animate attributeName="opacity" values="0;0;1;0;0" keyTimes="0;0.7;0.71;0.73;1" {loop}/>'
               f'<animateTransform attributeName="transform" type="translate" values="700 75;700 75;520 135;520 135" keyTimes="0;0.7;0.73;1" {loop}/></line>')
    out.append(f'<g><animateTransform attributeName="transform" type="translate" {arc_motion(0.5)}/>'
               '<circle r="52" fill="url(#moonglow)"/><circle r="21" fill="url(#moon)"/>'
               '<circle cx="-7" cy="-5" r="4.5" fill="#c4bea8" opacity="0.7"/><circle cx="7" cy="5" r="3.2" fill="#c4bea8" opacity="0.7"/>'
               '<circle cx="-3" cy="10" r="2.2" fill="#c4bea8" opacity="0.7"/><circle cx="10" cy="-8" r="1.8" fill="#c4bea8" opacity="0.7"/></g>')
    lights = "".join(
        f'<circle cx="{cx}" cy="5.5" r="1.6"><animate attributeName="fill" values="{v}" dur="1.2s" repeatCount="indefinite"/></circle>'
        for cx, v in ((-14, "#7ee787;#d29922;#ff7b72;#7ee787"), (0, "#d29922;#ff7b72;#7ee787;#d29922"), (14, "#ff7b72;#7ee787;#d29922;#ff7b72")))
    out.append(f'<g><animateTransform attributeName="transform" type="translate" values="-60 105;-60 105;400 105;420 98;440 105;1030 85;1030 85" keyTimes="0;0.6;0.68;0.74;0.8;0.88;1" {loop}/>'
               f'<polygon points="-7,6 7,6 30,150 -30,150" fill="url(#beam)" opacity="0"><animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.68;0.7;0.78;0.8;1" {loop}/></polygon>'
               '<ellipse cx="0" cy="-1" rx="9" ry="8" fill="#9ecbff" opacity="0.75"/><ellipse cx="0" cy="4" rx="24" ry="6" fill="#8b949e"/><ellipse cx="0" cy="2.5" rx="24" ry="3" fill="#c9d1d9"/>'
               f'{lights}</g>')
    out.append("</g>")

    # dia: sol com raios girando, nuvens, avião com rastro
    out.append(f'<g><animateTransform attributeName="transform" type="translate" {arc_motion(0)}/>'
               '<circle r="58" fill="url(#sunhalo)" opacity="0.8"/>'
               '<circle r="30" fill="url(#retro)" clip-path="url(#stripes)"/></g>')
    out.append(f'<g opacity="0"><animate attributeName="opacity" {day_on}/>')
    for cx, cy, k, dur, begin in ((200, 100, 1.1, 150, 0), (520, 140, 0.8, 190, 40), (760, 95, 1.2, 170, 90), (380, 170, 0.6, 210, 120), (880, 150, 0.7, 230, 60)):
        out.append(cloud(cx, cy, k, dur, begin))
    out.append(f'<g><animateTransform attributeName="transform" type="translate" values="1040 84;1040 84;-120 70;-120 70" keyTimes="0;0.1;0.38;1" {loop}/>'
               '<rect x="30" y="-2.2" width="110" height="2.4" rx="1.2" fill="url(#trail)"/>'
               '<path d="M0 0 Q2 -4 8 -4 L30 -4 Q34 -4 34 -1 Q34 2 30 2 L8 2 Q2 2 0 0 Z" fill="#eef2f7"/>'
               '<path d="M26 -4 L32 -12 L35 -12 L33 -4 Z" fill="#c9d1d9"/>'
               '<path d="M13 -1 L22 -10 L26 -10 L20 -1 Z M13 1 L22 9 L26 9 L20 1 Z" fill="#aab4c2"/>'
               '<rect x="5" y="-2.6" width="16" height="1.2" fill="#58a6ff" opacity="0.7"/>'
               '<circle cx="34" cy="-11" r="1.4" fill="#ff7b72"><animate attributeName="opacity" values="1;0.1;1" dur="1s" repeatCount="indefinite"/></circle></g>')
    out.append("</g>")

    # silhueta distante para dar profundidade
    x, far = 0.0, []
    while x < W:
        w, h = 18 + rnd() * 30, 30 + rnd() * 70
        far.append(f'<rect x="{x:.0f}" y="{ground - h:.0f}" width="{w:.0f}" height="{h:.0f}"/>')
        x += w + 2
    # quase some de dia para não pesar contra o céu claro
    out.append(f'<g fill="url(#far)" opacity="0.7"><animate attributeName="opacity" values="0.7;0.12;0.12;0.7;0.7" keyTimes="0;0.08;0.42;0.5;1" {loop}/>{"".join(far)}</g>')

    # prédios: um por semana, com sombra, borda iluminada e detalhes no topo
    windows = []
    for i, total in enumerate(weeks):
        h = 10 + (ground - 92) * (total / peak) ** 0.6
        x, y = x0 + i * (bw + gap), ground - h
        delay = i * 0.03
        grow = (f'<animate attributeName="height" from="0" to="{h:.1f}" dur="1.2s" begin="{delay:.2f}s" fill="freeze"/>'
                f'<animate attributeName="y" from="{ground}" to="{y:.1f}" dur="1.2s" begin="{delay:.2f}s" fill="freeze"/>')
        fill = "url(#bldhot)" if total >= peak * 0.4 else "url(#bld)"
        out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw}" height="{h:.1f}" fill="{fill}">{grow}</rect>')
        out.append(f'<rect x="{x + bw - 3:.1f}" y="{y:.1f}" width="3" height="{h:.1f}" fill="#000" opacity="0.28">{grow}</rect>')
        out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="1.4" height="{h:.1f}" fill="#9ecbff" opacity="0.25">{grow}</rect>')
        top = f'opacity="0"><animate attributeName="opacity" to="1" dur="0.4s" begin="{delay + 1.1:.2f}s" fill="freeze"/>'
        mid = x + bw / 2
        if total == peak:
            out.append(f'<g {top}<line x1="{mid:.1f}" y1="{y:.1f}" x2="{mid:.1f}" y2="{y - 16:.1f}" stroke="#8b949e" stroke-width="1.2"/>'
                       f'<circle cx="{mid:.1f}" cy="{y - 17:.1f}" r="2.4" fill="#ff7b72"><animate attributeName="opacity" values="1;0.1;1" dur="1.4s" repeatCount="indefinite"/></circle></g>')
        elif total >= peak * 0.55:
            out.append(f'<g {top}<rect x="{x - 1:.1f}" y="{y - 3:.1f}" width="{bw + 2}" height="3" fill="#2a3a60"/>'
                       f'<line x1="{x + 4:.1f}" y1="{y - 3:.1f}" x2="{x + 4:.1f}" y2="{y - 10:.1f}" stroke="#8b949e"/></g>')
        elif total >= peak * 0.25:
            out.append(f'<g {top}<rect x="{x + 4:.1f}" y="{y - 6:.1f}" width="6" height="6" rx="1" fill="#3a4a72"/></g>')
        for wy in range(int(y) + 6, ground - 8, 9):
            for wx in (x + 3, x + 8.5):
                if total and rnd() < 0.5:
                    color = "#ffcf6e" if rnd() < 0.82 else "#9ecbff"
                    flick = ""
                    if rnd() < 0.15:
                        flick = f'<animate attributeName="opacity" values="1;1;0.25;1" keyTimes="0;0.6;0.7;1" dur="{4 + rnd() * 6:.1f}s" repeatCount="indefinite"/>'
                    windows.append(f'<rect x="{wx:.1f}" y="{wy}" width="2.6" height="3.4" fill="{color}">{flick}</rect>')
    # janelas: reflexo fraco de dia, acesas à noite
    out.append(f'<g opacity="0.15"><animate attributeName="opacity" values="0.15;0.15;1;1;0.15" keyTimes="0;0.5;0.58;0.92;1" {loop}/>{"".join(windows)}</g>')

    # rua com postes que acendem à noite
    out.append(f'<rect y="{ground}" width="{W}" height="{H - ground}" fill="#05070d"/>')
    floor = H - 34  # a grade termina antes do rodapé
    grid = [f'<line x1="0" y1="{ground + (floor - ground) * (k / 7) ** 1.8:.1f}" x2="{W}" y2="{ground + (floor - ground) * (k / 7) ** 1.8:.1f}"/>' for k in range(1, 8)]
    grid += [f'<line x1="{W / 2 + dx * 0.12:.0f}" y1="{ground}" x2="{W / 2 + dx:.0f}" y2="{floor}"/>' for dx in range(-1600, 1601, 80)]
    out.append(f'<g stroke="{BLUE}" stroke-opacity="0.28" stroke-width="0.8">{"".join(grid)}</g>')
    out.append(f'<rect y="{floor}" width="{W}" height="{H - floor}" fill="#05070d"/>')
    out.append(f'<line x1="0" y1="{ground}" x2="{W}" y2="{ground}" stroke="{BLUE}" stroke-width="3" stroke-opacity="0.25"/>')
    out.append(f'<line x1="0" y1="{ground}" x2="{W}" y2="{ground}" stroke="url(#line)" stroke-width="1.2"/>')
    posts = range(40, W, 120)
    out.append("".join(f'<path d="M{lx} {ground} V{ground - 18} H{lx + 6}" fill="none" stroke="#4a5570" stroke-width="1.5"/>' for lx in posts))
    out.append(f'<g opacity="0"><animate attributeName="opacity" {night_on}/>'
               + "".join(f'<circle cx="{lx + 6}" cy="{ground - 16}" r="16" fill="url(#lamp)"/><circle cx="{lx + 6}" cy="{ground - 17}" r="1.8" fill="#ffd27a"/>' for lx in posts)
               + "</g>")

    out += [
        f'<text x="32" y="42" font-family="{FONT}" font-size="15" font-weight="700" letter-spacing="2" fill="{BLUE}" paint-order="stroke" stroke="#05070d" stroke-opacity="0.85" stroke-width="4">CONTRIBUTION.CITY'
        f'<tspan dx="14" font-weight="400" letter-spacing="0" font-size="13" fill="{SOFT}" paint-order="stroke" stroke="#05070d" stroke-opacity="0.85" stroke-width="4">&gt; cada prédio é uma semana</tspan></text>',
        f'<text x="{W - 32}" y="42" text-anchor="end" font-family="{FONT}" font-size="14" font-weight="700" fill="{INK}" paint-order="stroke" stroke="#05070d" stroke-opacity="0.85" stroke-width="4">{cal["totalContributions"]} contribuições no último ano</text>',
        f'<text x="32" y="{H - 14}" font-family="{FONT}" font-size="12" fill="{SOFT}" fill-opacity="0.8">dados do GitHub, atualizados todo dia por um GitHub Action</text>',
        "</g>",
        f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="18" fill="none" stroke="{BLUE}" stroke-opacity="0.5" stroke-width="1.5"/>',
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
