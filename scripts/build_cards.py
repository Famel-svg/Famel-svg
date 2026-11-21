"""Gera os cartões SVG do perfil (estatísticas e linguagens) a partir da API GraphQL do GitHub.

Substitui o github-readme-stats público. Uso: GITHUB_TOKEN=... python scripts/build_cards.py
"""
import json
import os
import random
import urllib.request
from datetime import date
from html import escape
from pathlib import Path
from xml.etree import ElementTree

from festive import GROUND, LAYERS as FESTIVE, _falling, festive_event

from panel import write_panel

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


EVENTS = ["chuva", "abducao", "tempestade", "fogos", "neblina", "balao", "neve"]
# um evento por dia: data festiva tem prioridade; senão sorteio (semente = data, então o dia todo mostra o mesmo); CITY_EVENT força um evento para testar
EVENT = (os.environ.get("CITY_EVENT") or festive_event(date.today())
         or random.Random(date.today().toordinal()).choice(EVENTS))


def event_layer(event, W, H, loop, rnd, road):
    """Camada do evento do dia, desenhada por cima da cidade."""
    if event in FESTIVE:
        return FESTIVE[event](W, H, loop, rnd, road)
    if event in ("chuva", "tempestade"):
        drops = []
        for _ in range(140):
            x, y, d = rnd() * (W + 200) - 100, rnd() * H, 0.6 + rnd() * 0.5
            drops.append(f'<line x1="{x:.0f}" y1="{y:.0f}" x2="{x - 5:.0f}" y2="{y + 14:.0f}">'
                         f'<animateTransform attributeName="transform" type="translate" values="0 -{H};-{H * 0.36:.0f} 0" dur="{d:.2f}s" begin="-{rnd() * d:.2f}s" repeatCount="indefinite"/></line>')
        rain = (f'<rect width="{W}" height="{H}" fill="#3d4a5c" opacity="{0.45 if event == "tempestade" else 0.32}"/>'
                f'<g stroke="#b9d4f0" stroke-width="1.1" stroke-opacity="0.55" stroke-linecap="round">{"".join(drops)}</g>')
        if event == "chuva":
            return rain
        # tempestade: raios em pontos e horários diferentes, com clarão na tela toda
        bolts = []
        for k, t in enumerate((0.12, 0.31, 0.47, 0.66, 0.83)):
            x, y = 120 + rnd() * (W - 240), 60.0
            pts = [(x, y)]
            while y < 300:
                y += 22 + rnd() * 18
                x += (rnd() - 0.5) * 40
                pts.append((x, y))
            kt = f'keyTimes="0;{t:.3f};{t + 0.003:.3f};{t + 0.008:.3f};{t + 0.011:.3f};{t + 0.016:.3f};1"'
            flash = f'values="0;0;1;0.2;1;0;0" {kt} {loop}'
            line = " ".join(f"{px:.0f},{py:.0f}" for px, py in pts)
            bolts.append(f'<rect width="{W}" height="{H}" fill="#e6f1ff" opacity="0"><animate attributeName="opacity" values="0;0;0.35;0.05;0.3;0;0" {kt} {loop}/></rect>'
                         f'<g opacity="0"><animate attributeName="opacity" {flash}/>'
                         f'<polyline points="{line}" fill="none" stroke="#9ecbff" stroke-width="5" stroke-opacity="0.4"/>'
                         f'<polyline points="{line}" fill="none" stroke="#ffffff" stroke-width="1.8"/></g>')
        return rain + "".join(bolts)
    if event == "abducao":
        # à noite o óvni chega, desce sobre a avenida, puxa um carro e vai embora
        rx_, ry_ = road
        hover = ry_ - 110
        kt = 'keyTimes="0;0.6;0.64;0.68;0.8;0.84;0.88;1"'
        ufo = (f'<g><animateTransform attributeName="transform" type="translate" values="-80 90;-80 90;{rx_:.0f} 90;{rx_:.0f} {hover:.0f};{rx_:.0f} {hover:.0f};{rx_:.0f} 70;1040 40;1040 40" {kt} {loop}/>'
               f'<polygon points="-8,6 8,6 30,110 -30,110" fill="url(#beam)" opacity="0"><animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.68;0.69;0.79;0.8;1" {loop}/></polygon>'
               '<ellipse cx="0" cy="-1" rx="10" ry="9" fill="#9ecbff" opacity="0.8"/><ellipse cx="0" cy="4" rx="28" ry="7" fill="#8b949e"/><ellipse cx="0" cy="2.5" rx="28" ry="3.5" fill="#c9d1d9"/>'
               + "".join(f'<circle cx="{cx}" cy="6.5" r="1.8" fill="#7ee787"><animate attributeName="fill" values="#7ee787;#ff7b72;#d29922;#7ee787" dur="0.8s" begin="{k * 0.2}s" repeatCount="indefinite"/></circle>' for k, cx in enumerate((-16, 0, 16)))
               + "</g>")
        car = (f'<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.62;0.63;0.775;0.78;1" {loop}/>'
               f'<animateTransform attributeName="transform" type="translate" values="-40 {ry_:.0f};-40 {ry_:.0f};{rx_:.0f} {ry_:.0f};{rx_:.0f} {ry_:.0f};{rx_:.0f} {hover + 8:.0f};{rx_:.0f} {hover + 8:.0f}" keyTimes="0;0.62;0.69;0.7;0.78;1" {loop}/>'
               f'<g><animateTransform attributeName="transform" type="rotate" values="0;0;-25;20;-15;0" keyTimes="0;0.7;0.72;0.74;0.76;1" {loop}/>'
               '<rect x="-9" y="-5" width="18" height="6" rx="2" fill="#ff7b72"/><rect x="-5" y="-8" width="10" height="4" rx="1.5" fill="#ffa198"/>'
               '<circle cx="-5" cy="1.5" r="1.8" fill="#161b22"/><circle cx="5" cy="1.5" r="1.8" fill="#161b22"/></g></g>')
        return car + ufo
    if event == "fogos":
        # à noite foguetes sobem e explodem em cores sobre os prédios
        import math
        out = []
        colors = ["#ff7b72", "#7ee787", "#58a6ff", "#d29922", "#f778ba", "#ffd166"]
        for k in range(12):
            t = 0.58 + k * 0.026
            x, y = 100 + rnd() * (W - 200), 90 + rnd() * 110
            col = colors[k % len(colors)]
            rise = f'keyTimes="0;{t:.3f};{t + 0.02:.3f};1"'
            # foguete: corpo, ponta, chama piscando e rastro de faíscas, subindo do chão até a explosão
            out.append(f'<g opacity="0">'
                       f'<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;{t:.3f};{t + 0.001:.3f};{t + 0.019:.3f};{t + 0.02:.3f};1" {loop}/>'
                       f'<animateTransform attributeName="transform" type="translate" values="{x:.0f} {H - 60};{x:.0f} {H - 60};{x:.0f} {y:.0f};{x:.0f} {y:.0f}" {rise} {loop}/>'
                       '<line x1="0" y1="8" x2="0" y2="30" stroke="#ffd166" stroke-width="2" stroke-opacity="0.5" stroke-linecap="round"/>'
                       '<circle cx="0" cy="12" r="2.6" fill="#ff9e3d"><animate attributeName="r" values="2.6;1.4;2.6" dur="0.12s" repeatCount="indefinite"/></circle>'
                       '<circle cx="-1.5" cy="20" r="1" fill="#ffd166"/><circle cx="1.5" cy="26" r="0.8" fill="#ffd166"/>'
                       f'<rect x="-2" y="-6" width="4" height="14" rx="1" fill="{col}"/>'
                       '<path d="M-2 -6 L0 -11 L2 -6 Z" fill="#e6f1ff"/></g>')
            b = t + 0.02
            bt = f'keyTimes="0;{b:.3f};{b + 0.025:.3f};1"'
            sparks = []
            for a in range(22):
                ang = a / 22 * 2 * math.pi
                dx, dy = math.cos(ang) * 80, math.sin(ang) * 80
                sparks.append(f'<circle r="3" fill="{col}"><animateTransform attributeName="transform" type="translate" values="0 0;0 0;{dx:.1f} {dy + 6:.1f};{dx:.1f} {dy + 6:.1f}" {bt} {loop}/></circle>')
            out.append(f'<g transform="translate({x:.0f} {y:.0f})" opacity="0">'
                       f'<animate attributeName="opacity" values="0;0;1;0;0" keyTimes="0;{b:.3f};{b + 0.004:.3f};{b + 0.05:.3f};1" {loop}/>'
                       f'<circle r="12" fill="{col}" opacity="0.45"/>{"".join(sparks)}</g>')
        return "".join(out)
    if event == "neblina":
        # faixas translúcidas passando devagar entre os prédios, mais densas perto do chão
        bands = []
        for k in range(7):
            y = road[1] - 170 + k * 30 + rnd() * 10
            w, dur = 500 + rnd() * 400, 40 + rnd() * 40
            bands.append(f'<ellipse cx="0" cy="{y:.0f}" rx="{w / 2:.0f}" ry="{14 + rnd() * 10:.0f}" fill="url(#fog)" opacity="{0.35 + k * 0.07:.2f}">'
                         f'<animateTransform attributeName="transform" type="translate" values="{-w / 2:.0f} 0;{W + w / 2:.0f} 0" dur="{dur:.0f}s" begin="-{rnd() * dur:.0f}s" repeatCount="indefinite"/></ellipse>')
        return ('<defs><radialGradient id="fog"><stop offset="0" stop-color="#dbe6f3" stop-opacity="0.75"/><stop offset="1" stop-color="#dbe6f3" stop-opacity="0"/></radialGradient>'
                '<linearGradient id="fogfade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#c9d6e6" stop-opacity="0"/><stop offset="1" stop-color="#c9d6e6" stop-opacity="0.22"/></linearGradient></defs>'
                f'<rect y="{road[1] - 200:.0f}" width="{W}" height="{H - road[1] + 200:.0f}" fill="url(#fogfade)"/>' + "".join(bands))
    if event == "neve":
        # céu acinzentado, flocos caindo devagar e calçada coberta de neve
        flakes = _falling(W, H, rnd, 160, lambda r: f'<circle r="{1 + r() * 2:.1f}" fill="#ffffff" opacity="{0.6 + r() * 0.4:.2f}"/>', dur=(6, 11), sway=24)
        return (f'<rect width="{W}" height="{H}" fill="#9aa8bb" opacity="0.22"/>'
                f'<rect y="{GROUND - 8}" width="{W}" height="16" rx="6" fill="#eef4fb" opacity="0.85"/>' + flakes)
    if event == "balao":
        # de dia um balão de ar quente atravessa o céu devagar, balançando
        return ('<defs><clipPath id="env"><ellipse cx="0" cy="0" rx="22" ry="26"/></clipPath></defs>'
                f'<g opacity="0"><animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;0.06;0.42;0.48;1" {loop}/>'
                f'<animateTransform attributeName="transform" type="translate" values="-60 170;300 120;650 150;1020 110;1020 110" keyTimes="0;0.15;0.3;0.46;1" {loop}/>'
                '<g><animateTransform attributeName="transform" type="translate" values="0 0;0 -6;0 0" dur="4s" repeatCount="indefinite"/>'
                '<g clip-path="url(#env)"><rect x="-22" y="-26" width="44" height="52" fill="#ff7b72"/>'
                '<rect x="-12" y="-26" width="8" height="52" fill="#ffd166"/><rect x="4" y="-26" width="8" height="52" fill="#58a6ff"/></g>'
                '<ellipse cx="-7" cy="-10" rx="5" ry="9" fill="#ffffff" opacity="0.25"/>'
                '<path d="M-14 20 L-6 36 M14 20 L6 36" stroke="#8b949e" stroke-width="1"/>'
                '<rect x="-7" y="36" width="14" height="9" rx="1.5" fill="#8b5a2b"/></g></g>')
    return ""


def city_card(user, layout="day"):
    """Cidade isométrica: cada quarteirão é uma semana, cada lote um dia; prédio cresce com as contribuições.

    Céu com ciclo de dia e noite de 60s: sol retrô, nuvens e avião de dia; lua, estrelas e óvni à noite.
    """
    cal = user["contributionsCollection"]["contributionCalendar"]
    days = [[d["contributionCount"] for d in w["contributionDays"]] for w in cal["weeks"]]
    W, H = 960, 560
    lots_xy, labels = {}, {}
    if layout == "day":
        BX = 12  # quarteirões por linha; cada quarteirão tem 3x3 lotes e uma rua de 1 lote
        cols, rows = BX * 4, -(-len(days) // BX) * 4
        street_r, street_c = list(range(3, rows - 1, 4)), list(range(3, cols - 1, 4))
        rx, ry, oy, hmax = 4.0, 12.5, 240.0, 60
        # 7 dias ocupam o quarteirão 3x3; os 2 cantos da frente viram praça
        SPOTS = [(0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1), (1, 2)]
        for k, wk in enumerate(days):
            bc, br = (k % BX) * 4, (k // BX) * 4
            for d, n in enumerate(wk):
                lots_xy[bc + SPOTS[d][0], br + SPOTS[d][1]] = n
            for dc, dr in ((0, 2), (2, 2)):
                lots_xy[bc + dc, br + dr] = 0
        tagline = "cada quarteirão é uma semana, cada lote um dia"
    elif layout == "week":
        # um prédio por semana, em duas avenidas
        half = -(-len(days) // 2)
        cols, rows = half, 3
        street_r, street_c = [1], []
        rx, ry, oy, hmax = 14.0, 26.0, 430.0, 270
        for k, wk in enumerate(days):
            lots_xy[k % half, 0 if k < half else 2] = sum(wk)
        tagline = "cada prédio é uma semana"
    else:
        # um prédio por mês, com o nome embaixo
        months = {}
        for wk in cal["weeks"]:
            for d in wk["contributionDays"]:
                key = d["date"][:7]
                months[key] = months.get(key, 0) + d["contributionCount"]
        keys = sorted(months)[-12:]
        cols, rows = len(keys), 1
        street_r, street_c = [], []
        rx, ry, oy, hmax = 10.0, 28.0, 400.0, 250
        NOMES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
        for c, key in enumerate(keys):
            lots_xy[c, 0] = months[key]
            labels[c] = (NOMES[int(key[5:]) - 1], months[key])
        tagline = "cada prédio é um mês"
    peak = max(lots_xy.values(), default=0) or 1
    # vista frontal inclinada: o tempo corre na horizontal, a profundidade desce para a esquerda
    # plataforma passa das bordas: os cantos inclinados ficam fora do quadro e ela acompanha o chão
    ox = 12 + rows * rx * 0.5
    sx = (W - ox + rows * rx + 12) / cols
    seed = 7

    def rnd():
        nonlocal seed
        seed = (seed * 1103515245 + 12345) % 2**31
        return seed / 2**31

    def P(c, r, z=0.0):
        return ox + c * sx - r * rx, oy + r * ry - z

    def poly(pts, fill, extra=""):
        return f'<polygon points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts)}" fill="{fill}"{extra}/>'

    loop = 'dur="60s" repeatCount="indefinite"'
    # metade dia (0-0.5), metade noite (0.5-1); transições de 0.08
    day_on = f'values="0;1;1;0;0" keyTimes="0;0.08;0.42;0.5;1" {loop}'
    night_on = f'values="0;0;1;1;0" keyTimes="0;0.5;0.58;0.92;1" {loop}'
    dusk = f'values="0.8;0;0;0.8;0;0;0.8" keyTimes="0;0.08;0.42;0.5;0.58;0.92;1" {loop}'
    arc = "-70 230;90 150;260 110;480 95;700 110;870 150;1030 230"

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
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Cidade animada das contribuições no GitHub: {cal["totalContributions"]} no último ano">',
        "<defs>",
        '<linearGradient id="night" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#05070d"/><stop offset="0.55" stop-color="#0d1a33"/><stop offset="1" stop-color="#05070d"/></linearGradient>',
        '<radialGradient id="o1"><stop offset="0" stop-color="#58a6ff" stop-opacity="0.45"/><stop offset="0.6" stop-color="#58a6ff" stop-opacity="0.1"/><stop offset="1" stop-color="#58a6ff" stop-opacity="0"/></radialGradient>',
        '<radialGradient id="o2"><stop offset="0" stop-color="#3fb950" stop-opacity="0.35"/><stop offset="0.6" stop-color="#3fb950" stop-opacity="0.08"/><stop offset="1" stop-color="#3fb950" stop-opacity="0"/></radialGradient>',
        '<linearGradient id="day" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2f7fd1"/><stop offset="0.65" stop-color="#8cc4ee"/><stop offset="1" stop-color="#f6d7a7"/></linearGradient>',
        '<linearGradient id="dusk" x1="0" y1="0" x2="0" y2="1"><stop offset="0.35" stop-color="#ff8c42" stop-opacity="0"/><stop offset="1" stop-color="#ff6b3d" stop-opacity="0.85"/></linearGradient>',
        '<radialGradient id="sunhalo"><stop offset="0.3" stop-color="#ffe29a" stop-opacity="0.7"/><stop offset="1" stop-color="#ffe29a" stop-opacity="0"/></radialGradient>',
        '<radialGradient id="soft"><stop offset="0" stop-color="#fff6d8"/><stop offset="0.75" stop-color="#ffe7a3"/><stop offset="1" stop-color="#ffd166"/></radialGradient>',
        '<linearGradient id="retro" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffe08a"/><stop offset="1" stop-color="#ff7a45"/></linearGradient>',
        '<clipPath id="stripes"><rect x="-30" y="-30" width="60" height="31"/><rect x="-30" y="4" width="60" height="5"/><rect x="-30" y="12" width="60" height="4"/><rect x="-30" y="19" width="60" height="3"/><rect x="-30" y="25" width="60" height="5"/></clipPath>',
        '<radialGradient id="moonglow"><stop offset="0.4" stop-color="#dfe9ff" stop-opacity="0.4"/><stop offset="1" stop-color="#dfe9ff" stop-opacity="0"/></radialGradient>',
        '<radialGradient id="moon" cx="0.35" cy="0.35"><stop offset="0" stop-color="#fbfaf2"/><stop offset="1" stop-color="#cfcab6"/></radialGradient>',
        '<linearGradient id="cloud" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffffff"/><stop offset="1" stop-color="#e3ebf5"/></linearGradient>',
        '<linearGradient id="trail" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#ffffff" stop-opacity="0.8"/><stop offset="1" stop-color="#ffffff" stop-opacity="0"/></linearGradient>',
        '<linearGradient id="beam" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#7ee787" stop-opacity="0.5"/><stop offset="1" stop-color="#7ee787" stop-opacity="0"/></linearGradient>',
        '<linearGradient id="line" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#58a6ff"/><stop offset="1" stop-color="#3fb950"/></linearGradient>',
        f'<clipPath id="frame"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="18"/></clipPath>',
        "</defs>",
        '<g clip-path="url(#frame)">',
        f'<rect width="{W}" height="{H}" fill="url(#night)"/>',
        f'<circle cx="100" cy="20" r="340" fill="url(#o1)"/><circle cx="{W - 70}" cy="{H - 10}" r="320" fill="url(#o2)"/>',
        f'<rect width="{W}" height="{H}" fill="url(#day)" opacity="0"><animate attributeName="opacity" {day_on}/></rect>',
        f'<rect width="{W}" height="{H}" fill="url(#dusk)" opacity="0"><animate attributeName="opacity" {dusk}/></rect>',
    ]

    # noite: estrelas, estrela cadente, lua, óvni
    out.append(f'<g opacity="0"><animate attributeName="opacity" {night_on}/>')
    for _ in range(110):
        x, y, r, d = rnd() * W, 62 + rnd() * 300, 0.4 + rnd() * 1.2, 2 + rnd() * 4
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" fill="#f0f6fc"><animate attributeName="opacity" values="0.2;1;0.2" dur="{d:.1f}s" begin="{rnd() * 3:.1f}s" repeatCount="indefinite"/></circle>')
    out.append(f'<line x1="0" y1="0" x2="70" y2="22" stroke="url(#trail)" stroke-width="1.6" stroke-linecap="round" opacity="0">'
               f'<animate attributeName="opacity" values="0;0;1;0;0" keyTimes="0;0.7;0.71;0.73;1" {loop}/>'
               f'<animateTransform attributeName="transform" type="translate" values="760 80;760 80;580 140;580 140" keyTimes="0;0.7;0.73;1" {loop}/></line>')
    out.append(f'<g><animateTransform attributeName="transform" type="translate" {arc_motion(0.5)}/>'
               '<circle r="52" fill="url(#moonglow)"/><circle r="21" fill="url(#moon)"/>'
               '<circle cx="-7" cy="-5" r="4.5" fill="#c4bea8" opacity="0.7"/><circle cx="7" cy="5" r="3.2" fill="#c4bea8" opacity="0.7"/>'
               '<circle cx="-3" cy="10" r="2.2" fill="#c4bea8" opacity="0.7"/><circle cx="10" cy="-8" r="1.8" fill="#c4bea8" opacity="0.7"/></g>')
    lights = "".join(
        f'<circle cx="{cx}" cy="5.5" r="1.6"><animate attributeName="fill" values="{v}" dur="1.2s" repeatCount="indefinite"/></circle>'
        for cx, v in ((-14, "#7ee787;#d29922;#ff7b72;#7ee787"), (0, "#d29922;#ff7b72;#7ee787;#d29922"), (14, "#ff7b72;#7ee787;#d29922;#ff7b72")))
    if EVENT != "abducao" and EVENT not in FESTIVE:  # abdução tem o próprio óvni; datas festivas ficam sem, para não poluir
        out.append(f'<g><animateTransform attributeName="transform" type="translate" values="1030 110;1030 110;500 120;480 113;460 120;-60 80;-60 80" keyTimes="0;0.6;0.68;0.74;0.8;0.88;1" {loop}/>'
                   f'<polygon points="-7,6 7,6 40,190 -40,190" fill="url(#beam)" opacity="0"><animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.68;0.7;0.78;0.8;1" {loop}/></polygon>'
                   '<ellipse cx="0" cy="-1" rx="9" ry="8" fill="#9ecbff" opacity="0.75"/><ellipse cx="0" cy="4" rx="24" ry="6" fill="#8b949e"/><ellipse cx="0" cy="2.5" rx="24" ry="3" fill="#c9d1d9"/>'
                   f'{lights}</g>')
    out.append("</g>")

    # dia: sol retrô, nuvens, avião com rastro
    out.append(f'<g><animateTransform attributeName="transform" type="translate" {arc_motion(0)}/>'
               '<circle r="56" fill="url(#sunhalo)"><animate attributeName="r" values="50;60;50" dur="5s" repeatCount="indefinite"/></circle>'
               '<circle r="24" fill="url(#soft)"/></g>')
    out.append(f'<g opacity="0"><animate attributeName="opacity" {day_on}/>')
    for cx, cy, k, dur, begin in ((180, 100, 1.0, 150, 0), (520, 150, 0.8, 190, 40), (780, 90, 1.1, 170, 90), (380, 190, 0.6, 210, 120), (900, 170, 0.7, 230, 60)):
        out.append(cloud(cx, cy, k, dur, begin))
    out.append(f'<g><animateTransform attributeName="transform" type="translate" values="1040 150;1040 150;-120 66;-120 66" keyTimes="0;0.1;0.38;1" {loop}/>'
               '<rect x="30" y="-2.2" width="110" height="2.4" rx="1.2" fill="url(#trail)"/>'
               '<path d="M0 0 Q2 -4 8 -4 L30 -4 Q34 -4 34 -1 Q34 2 30 2 L8 2 Q2 2 0 0 Z" fill="#eef2f7"/>'
               '<path d="M26 -4 L32 -12 L35 -12 L33 -4 Z" fill="#c9d1d9"/>'
               '<path d="M13 -1 L22 -10 L26 -10 L20 -1 Z M13 1 L22 9 L26 9 L20 1 Z" fill="#aab4c2"/>'
               '<rect x="5" y="-2.6" width="16" height="1.2" fill="#58a6ff" opacity="0.7"/>'
               '<circle cx="34" cy="-11" r="1.4" fill="#ff7b72"><animate attributeName="opacity" values="1;0.1;1" dur="1s" repeatCount="indefinite"/></circle></g>')
    out.append("</g>")

    # plataforma em losango com espessura
    N, E, S, Wc = P(-0.5, -0.5), P(cols - 0.5, -0.5), P(cols - 0.5, rows - 0.5), P(-0.5, rows - 0.5)
    slab = 10
    # calçada da frente: preenche até o rodapé para não sobrar céu embaixo da cidade
    out.append(f'<rect x="0" y="{N[1]:.1f}" width="{W}" height="{H - N[1]:.1f}" fill="#0a1226"/>')
    out.append(f'<line x1="0" y1="{S[1] + slab:.1f}" x2="{W}" y2="{S[1] + slab:.1f}" stroke="{BLUE}" stroke-opacity="0.35"/>')
    out.append(poly([Wc, S, (S[0], S[1] + slab), (Wc[0], Wc[1] + slab)], "#0a1226"))
    out.append(poly([S, E, (E[0], E[1] + slab), (S[0], S[1] + slab)], "#070d1c"))
    out.append(poly([N, E, S, Wc], "#0f1d3d", f' stroke="{BLUE}" stroke-opacity="0.7" stroke-width="1.2"'))
    # ruas tracejadas entre as fileiras
    out.append(f'<g stroke="{BLUE}" stroke-opacity="0.35" stroke-width="0.8" stroke-dasharray="3 3">'
               + "".join(f'<line x1="{P(-0.5, k + 0.5)[0]:.1f}" y1="{P(-0.5, k + 0.5)[1]:.1f}" x2="{P(cols - 0.5, k + 0.5)[0]:.1f}" y2="{P(cols - 0.5, k + 0.5)[1]:.1f}"/>' for k in street_r)
               + "".join(f'<line x1="{P(k + 0.5, -0.5)[0]:.1f}" y1="{P(k + 0.5, -0.5)[1]:.1f}" x2="{P(k + 0.5, rows - 0.5)[0]:.1f}" y2="{P(k + 0.5, rows - 0.5)[1]:.1f}"/>' for k in street_c)
               + "</g>")

    # lotes e árvores nos dias sem contribuição
    lots, trees = [], {}
    for (c, r), n in lots_xy.items():
        if True:
            i = 0.12
            lots.append(poly([P(c + i, r + i), P(c + 1 - i, r + i), P(c + 1 - i, r + 1 - i), P(c + i, r + 1 - i)], "#18284c"))
            if n == 0 and rnd() < 0.55:
                tx, ty = P(c + 0.5, r + 0.5)
                trees[c, r] = (f'<line x1="{tx:.1f}" y1="{ty:.1f}" x2="{tx:.1f}" y2="{ty - 3:.1f}" stroke="#5a4632" stroke-width="1"/>'
                             f'<circle cx="{tx:.1f}" cy="{ty - 5:.1f}" r="{2.6 + rnd():.1f}" fill="#2ea043"/><circle cx="{tx - 0.8:.1f}" cy="{ty - 5.8:.1f}" r="1.1" fill="#56d364" opacity="0.7"/>')
    out.append("".join(lots))

    # carros andando nas ruas, com farol de dia e de noite
    roads = [(P(-0.5, k + 0.5), P(cols - 0.5, k + 0.5)) for k in street_r] + [(P(k + 0.5, -0.5), P(k + 0.5, rows - 0.5)) for k in street_c]
    for j, (a, b) in enumerate(roads):
        rev, dur, begin = j % 2 == 1, 14 + (j * 3) % 9, (j * 5) % 13
        if rev:
            a, b = b, a
        color = "#ffd27a" if not rev else "#ff7b72"
        out.append(f'<circle r="1.8" fill="{color}"><animateMotion path="M{a[0]:.1f},{a[1]:.1f} L{b[0]:.1f},{b[1]:.1f}" dur="{dur}s" begin="-{begin}s" repeatCount="indefinite"/></circle>')

    # prédios: de trás para frente para a sobreposição ficar certa; janelas dentro de cada prédio
    TONES = [("#3a5aa0", "#24376a", "#16213f", "#6f95e6"), ("#3b4f86", "#22305c", "#141c38", "#6a84c8"), ("#2f5f8f", "#1f3d63", "#13253d", "#5fa0d6")]
    dim = f'<animate attributeName="opacity" values="0.12;0.12;1;1;0.12" keyTimes="0;0.5;0.58;0.92;1" {loop}/>'
    cells = sorted(((c, r, n) for (c, r), n in lots_xy.items()), key=lambda t: (t[1], t[0]))
    for c, r, n in cells:
        if not n:
            out.append(trees.get((c, r), ""))
            continue
        h = 8 + hmax * (n / peak) ** 0.55
        i = 0.16  # vão entre prédios vizinhos
        n_, e_, s_, w_ = P(c + i, r + i), P(c + 1 - i, r + i), P(c + 1 - i, r + 1 - i), P(c + i, r + 1 - i)
        up = lambda p, z=h: (p[0], p[1] - z)
        delay = 0.4 + c * 0.03
        top, front, side, rim = TONES[int(rnd() * len(TONES))]
        if n >= peak * 0.4:
            top, rim = "#5b82d6", "#9ecbff"
        # sombra no chão, para a direita
        # fundo deslocado para a direita: as faces visíveis são a fachada (w->s) e a lateral direita (s->e)
        body = poly([w_, s_, up(s_), up(w_)], front)
        body += poly([s_, e_, up(e_), up(s_)], side)
        body += poly([up(n_), up(e_), up(s_), up(w_)], top, f' stroke="{rim}" stroke-opacity="0.8" stroke-width="0.7"')
        # contorno neon nas quinas: brilho largo e fraco por baixo, traço fino por cima
        edges = [(w_, up(w_)), (s_, up(s_)), (e_, up(e_)), (up(w_), up(s_)), (up(s_), up(e_)), (up(e_), up(n_)), (up(n_), up(w_))]
        path = "".join(f"M{a[0]:.1f} {a[1]:.1f}L{b[0]:.1f} {b[1]:.1f}" for a, b in edges)
        body += (f'<path d="{path}" fill="none" stroke="{BLUE}" stroke-width="3" stroke-opacity="0.25" stroke-linecap="round"/>'
                 f'<path d="{path}" fill="none" stroke="#9ecbff" stroke-width="0.9" stroke-opacity="0.9" stroke-linecap="round"/>')
        mid = up(P(c + 0.5, r + 0.5))
        if n == peak:
            body += (f'<line x1="{mid[0]:.1f}" y1="{mid[1]:.1f}" x2="{mid[0]:.1f}" y2="{mid[1] - 14:.1f}" stroke="#8b949e" stroke-width="1"/>'
                     f'<circle cx="{mid[0]:.1f}" cy="{mid[1] - 15:.1f}" r="2" fill="#ff7b72"><animate attributeName="opacity" values="1;0.1;1" dur="1.4s" repeatCount="indefinite"/></circle>')
        elif h > 30:
            k = 0.3  # casinha de máquinas no telhado
            a1, b1, c1, d1 = P(c + k, r + k, h), P(c + 1 - k, r + k, h), P(c + 1 - k, r + 1 - k, h), P(c + k, r + 1 - k, h)
            hb = 3.5
            body += poly([d1, c1, (c1[0], c1[1] - hb), (d1[0], d1[1] - hb)], front) + poly([(a1[0], a1[1] - hb), (b1[0], b1[1] - hb), (c1[0], c1[1] - hb), (d1[0], d1[1] - hb)], top)
        # janelas: 3 colunas na frente, 1 na lateral
        wins = []
        for z in range(6, int(h) - 5, 9):
            for a, b, ts, tw in ((w_, s_, (0.18, 0.6), 0.2), (s_, e_, (0.35,), 0.3)):
                for t in ts:
                    if rnd() < 0.3:
                        p1 = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t - z)
                        p2 = (a[0] + (b[0] - a[0]) * (t + tw), a[1] + (b[1] - a[1]) * (t + tw) - z)
                        color = "#ffcf6e" if rnd() < 0.8 else "#9ecbff"
                        wins.append(poly([p1, p2, (p2[0], p2[1] - 3), (p1[0], p1[1] - 3)], color))
        if wins:
            body += f'<g opacity="0.12">{dim}{"".join(wins)}</g>'
        out.append(f'<g opacity="0"><animate attributeName="opacity" to="1" dur="0.5s" begin="{delay:.2f}s" fill="freeze"/>{body}</g>')

    # rótulos do layout por mês: nome na frente da plataforma e total acima do prédio
    for c, (name, v) in labels.items():
        fx, fy = P(c + 0.5, rows - 0.5)
        tx, ty = P(c + 0.5, 0.5, 8 + hmax * (v / peak) ** 0.55)
        out.append(f'<text x="{fx:.1f}" y="{fy + slab + 16:.1f}" text-anchor="middle" font-family="{FONT}" font-size="13" font-weight="700" fill="{INK}" paint-order="stroke" stroke="#05070d" stroke-opacity="0.8" stroke-width="3">{name}</text>')
        out.append(f'<text x="{tx:.1f}" y="{ty - 22:.1f}" text-anchor="middle" font-family="{FONT}" font-size="12" font-weight="700" fill="{INK}" paint-order="stroke" stroke="#05070d" stroke-opacity="0.8" stroke-width="3">{v}</text>')

    road = ((roads[0][0][0] + roads[0][1][0]) / 2, roads[0][0][1]) if roads else (W / 2, H - 80)
    out.append(event_layer(EVENT, W, H, loop, rnd, road))

    halo = 'paint-order="stroke" stroke="#05070d" stroke-opacity="0.85" stroke-width="4"'
    out += [
        f'<rect y="{H - 36}" width="{W}" height="36" fill="#05070d" opacity="0.85"/>',
        f'<line x1="0" y1="{H - 36}" x2="{W}" y2="{H - 36}" stroke="url(#line)" stroke-opacity="0.6"/>',
        f'<text x="32" y="42" font-family="{FONT}" font-size="15" font-weight="700" letter-spacing="2" fill="{BLUE}" {halo}>CONTRIBUTION.CITY'
        f'<tspan dx="14" font-weight="400" letter-spacing="0" font-size="13" fill="{SOFT}">&gt; {tagline}</tspan></text>',
        f'<text x="{W - 32}" y="42" text-anchor="end" font-family="{FONT}" font-size="14" font-weight="700" fill="{INK}" {halo}>{cal["totalContributions"]} contribuições no último ano</text>',
        f'<text x="32" y="{H - 14}" font-family="{FONT}" font-size="12" fill="{SOFT}" fill-opacity="0.8">dados do GitHub, atualizados todo dia por um GitHub Action</text>',
        "</g>",
        f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="18" fill="none" stroke="{BLUE}" stroke-opacity="0.5" stroke-width="1.5"/>',
        "</svg>",
    ]
    return "\n".join(out)


EN = {
    "Contribuições no último ano": "Contributions in the last year", "Commits no último ano": "Commits in the last year",
    "Repositórios públicos": "Public repositories", "Estrelas recebidas": "Stars received",
    "Estatísticas e linguagens": "Stats and languages", "linguagens": "languages",
    "Cidade animada das contribuições no GitHub": "Animated city of GitHub contributions", "no último ano": "in the last year",
    "cada quarteirão é uma semana, cada lote um dia": "each block is a week, each lot a day",
    "cada prédio é uma semana": "each building is a week", "cada prédio é um mês": "each building is a month",
    "contribuições no último ano": "contributions in the last year",
    "dados do GitHub, atualizados todo dia por um GitHub Action": "GitHub data, updated daily by a GitHub Action",
}


def to_en(svg):
    # ordem importa: frases longas antes das curtas que elas contêm
    for pt in sorted(EN, key=len, reverse=True):
        svg = svg.replace(pt, EN[pt])
    return svg


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
    city = city_card(user, "week")
    cards = [("stats.svg", stats), ("languages.svg", langs), ("overview.svg", pair), ("city.svg", city)]
    # versões em inglês para versions/README-en.md: mesmos cartões, só com os textos trocados
    cards += [("overview-en.svg", to_en(pair)), ("city-en.svg", to_en(city))]
    for name, svg in cards:
        ElementTree.fromstring(svg)  # self-check: SVG bem formado
        (OUT / name).write_text(svg, encoding="utf-8")
        print(f"wrote assets/{name}")
        if name in ("overview.svg", "city.svg", "overview-en.svg", "city-en.svg"):  # versões com painel para o README em imagens
            panel = write_panel(OUT / name)
            if panel:
                print(f"wrote {panel.name}")


if __name__ == "__main__":
    main()
