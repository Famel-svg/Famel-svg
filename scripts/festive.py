"""Eventos temáticos de datas festivas para a cidade (substituem o sorteio do dia).

Cada camada recebe (W, H, loop, rnd, road), igual a event_layer em build_cards.py.
Ciclo de 60s: dia em 0-0.5, noite em 0.5-1.
"""
import math
from datetime import date, timedelta


def easter(year):
    # algoritmo de Meeus/Jones/Butcher (calendário gregoriano)
    a, b, c = year % 19, year // 100, year % 100
    d, e = b // 4, b % 4
    g = (8 * b + 13) // 25
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 19 * l) // 433
    month = (h + l - 7 * m + 90) // 25
    return date(year, month, (h + l - 7 * m + 33 * month + 19) % 32)


def festive_event(d):
    """Evento festivo da data, ou None para cair no sorteio normal."""
    md = (d.month, d.day)
    if md == (12, 31) or md == (1, 1):
        return "anonovo"
    if (12, 20) <= md <= (12, 25):
        return "natal"
    if (10, 25) <= md <= (10, 31):
        return "halloween"
    if (6, 12) <= md <= (6, 29):
        return "junina"
    p = easter(d.year)
    if p - timedelta(days=50) <= d <= p - timedelta(days=46):  # sábado de carnaval até quarta de cinzas
        return "carnaval"
    if p - timedelta(days=2) <= d <= p:  # sexta-feira santa até domingo
        return "pascoa"
    return None


GROUND = 514  # faixa da calçada da frente, abaixo da plataforma e acima do rodapé


def _falling(W, H, rnd, n, shape, dur=(4.0, 7.0), sway=18):
    """Partículas caindo com balanço lateral (neve, confete)."""
    out = []
    for _ in range(n):
        x, d = rnd() * W, dur[0] + rnd() * (dur[1] - dur[0])
        s = rnd() * sway
        out.append(f'<g transform="translate({x:.0f} 0)"><g>'
                   f'<animateTransform attributeName="transform" type="translate" values="0 -20;{s:.0f} {H * 0.5:.0f};{-s:.0f} {H + 20}" dur="{d:.1f}s" begin="-{rnd() * d:.1f}s" repeatCount="indefinite"/>'
                   f'{shape(rnd)}</g></g>')
    return "".join(out)


def _garland(W, y0, sag, n_spans, item):
    """Cordão em arcos de lado a lado do céu, com um item a cada passo."""
    out, span = [], W / n_spans
    for s in range(n_spans):
        x0 = s * span
        out.append(f'<path d="M{x0:.0f} {y0} Q{x0 + span / 2:.0f} {y0 + sag * 2} {x0 + span:.0f} {y0}" fill="none" stroke="#8b949e" stroke-width="0.8" stroke-opacity="0.7"/>')
        for k in range(1, 8):
            t = k / 8
            x = x0 + span * t
            y = y0 + sag * 4 * t * (1 - t)
            out.append(item(x, y, s * 8 + k))
    return "".join(out)


def natal(W, H, loop, rnd, road):
    snow = _falling(W, H, rnd, 120, lambda r: f'<circle r="{1 + r() * 1.8:.1f}" fill="#ffffff" opacity="{0.6 + r() * 0.4:.2f}"/>')
    colors = ["#ff7b72", "#7ee787", "#ffd166", "#58a6ff"]
    lights = _garland(W, 64, 16, 5, lambda x, y, k: (
        f'<circle cx="{x:.0f}" cy="{y + 3:.0f}" r="2.6" fill="{colors[k % 4]}">'
        f'<animate attributeName="opacity" values="1;0.25;1" dur="1.4s" begin="{(k % 3) * 0.45:.2f}s" repeatCount="indefinite"/></circle>'))
    # trenó com renas cruzando o céu à noite
    deer = "".join(f'<g transform="translate({34 + j * 20} 0)"><ellipse cx="0" cy="0" rx="7" ry="3.2" fill="#8b5a2b"/>'
                   '<path d="M5 -2 L8 -7 M7 -6 L10 -8 M6 -6 L5 -9" stroke="#8b5a2b" stroke-width="1"/>'
                   '<path d="M-4 2 L-5 7 M4 2 L5 7" stroke="#8b5a2b" stroke-width="1"/></g>' for j in range(3))
    nose = '<circle cx="84" cy="-2" r="1.6" fill="#ff3b30"><animate attributeName="opacity" values="1;0.3;1" dur="0.6s" repeatCount="indefinite"/></circle>'
    sleigh = ('<path d="M-12 -6 L12 -6 L14 2 L-10 2 Z" fill="#da3633"/><path d="M-14 5 L16 5 Q20 5 19 1" fill="none" stroke="#ffd166" stroke-width="1.4"/>'
              '<circle cx="2" cy="-10" r="3.5" fill="#ffe0c2"/><path d="M-2 -12 L2 -20 L6 -12 Z" fill="#da3633"/><circle cx="2" cy="-20" r="1.4" fill="#ffffff"/>'
              '<line x1="12" y1="-3" x2="30" y2="-1" stroke="#8b949e" stroke-width="0.6"/>')
    ride = (f'<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.6;0.61;0.82;0.83;1" {loop}/>'
            f'<g><animateTransform attributeName="transform" type="translate" values="-120 160;-120 160;1060 90;1060 90" keyTimes="0;0.6;0.83;1" {loop}/>'
            f'{deer}{nose}{sleigh}</g></g>')
    return snow + lights + ride


def anonovo(W, H, loop, rnd, road):
    from build_cards import event_layer  # reaproveita os fogos e soma mais uma leva
    today = date.today()
    year = today.year + 1 if today.month == 12 else today.year
    text = (f'<text x="{W / 2}" y="170" text-anchor="middle" font-family="Consolas,monospace" font-size="72" font-weight="700" '
            f'fill="#ffd166" stroke="#ff7b72" stroke-width="1.5" opacity="0" paint-order="stroke">'
            f'<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.86;0.88;0.97;0.99;1" {loop}/>{year}</text>')
    # duas levas de fogos (rnd avança, então caem em pontos diferentes) e o ano no céu
    return event_layer("fogos", W, H, loop, rnd, road) + event_layer("fogos", W, H, loop, rnd, road) + text


def halloween(W, H, loop, rnd, road):
    night = 'values="0;0;1;1;0" keyTimes="0;0.5;0.58;0.92;1"'
    tint = f'<rect width="{W}" height="{H}" fill="#6e2a8c" opacity="0"><animate attributeName="opacity" values="0;0;0.22;0.22;0" keyTimes="0;0.5;0.58;0.92;1" {loop}/></rect>'
    # lua laranja por cima da lua normal, no mesmo arco
    arc = "-70 230;-70 230;90 150;260 110;480 95;700 110;870 150;1030 230"
    kt = "0;" + ";".join(f"{0.5 + k * 0.5 / 6:.3f}" for k in range(7))
    moon = (f'<g opacity="0"><animate attributeName="opacity" {night} {loop}/>'
            f'<g><animateTransform attributeName="transform" type="translate" values="{arc}" keyTimes="{kt}" {loop}/>'
            '<circle r="24" fill="#ff9e3d" opacity="0.85"/><circle r="46" fill="#ff9e3d" opacity="0.15"/></g></g>')
    bats = []
    for k in range(9):
        y, d, s = 80 + rnd() * 120, 9 + rnd() * 8, 1.2 + rnd() * 0.8
        wing = (f'<path d="M0 0 Q-6 -6 -12 -2 Q-8 -1 -6 2 Q-3 0 0 2 Q3 0 6 2 Q8 -1 12 -2 Q6 -6 0 0 Z" fill="#2a1d3a" stroke="#bc8cff" stroke-width="0.7" stroke-opacity="0.8">'
                f'<animateTransform attributeName="transform" type="scale" values="1 1;1 -0.4;1 1" dur="0.35s" repeatCount="indefinite"/></path>')
        bats.append(f'<g><animateTransform attributeName="transform" type="translate" values="{-30:.0f} {y:.0f};{W / 2:.0f} {y - 40:.0f};{W + 30} {y:.0f}" dur="{d:.1f}s" begin="-{rnd() * d:.1f}s" repeatCount="indefinite"/>'
                    f'<g transform="scale({s:.2f})">{wing}</g></g>')
    pumpkins = []
    for k in range(8):
        x = 60 + k * (W - 120) / 7 + rnd() * 20
        pumpkins.append(f'<g transform="translate({x:.0f} {GROUND})">'
                        '<ellipse cx="0" cy="0" rx="9" ry="7" fill="#e8741a"/><ellipse cx="0" cy="0" rx="3.5" ry="7" fill="#f08a2c"/>'
                        '<rect x="-1" y="-10" width="2" height="4" fill="#3fb950"/>'
                        '<path d="M-5 -2 L-3 -4 L-1 -2 Z M1 -2 L3 -4 L5 -2 Z M-4 2 Q0 5 4 2" fill="#ffd166" stroke="#ffd166" stroke-width="0.6">'
                        '<animate attributeName="opacity" values="1;0.5;1" dur="1.1s" repeatCount="indefinite"/></path></g>')
    return tint + moon + f'<g opacity="0"><animate attributeName="opacity" {night} {loop}/>{"".join(bats)}</g>' + "".join(pumpkins)


def carnaval(W, H, loop, rnd, road):
    colors = ["#ff7b72", "#7ee787", "#58a6ff", "#ffd166", "#f778ba", "#bc8cff"]
    confetti = _falling(W, H, rnd, 140, lambda r: (
        f'<rect x="-2" y="-3" width="4" height="6" fill="{colors[int(r() * 6)]}">'
        f'<animateTransform attributeName="transform" type="rotate" values="0;360" dur="{0.8 + r():.1f}s" repeatCount="indefinite"/></rect>'), dur=(5, 9), sway=30)
    beams = []
    for k in range(5):
        x, col, d = 120 + k * (W - 240) / 4, colors[k], 3 + k * 0.7
        beams.append(f'<polygon points="{x - 4:.0f},{GROUND} {x + 4:.0f},{GROUND} {x + 60:.0f},60 {x - 60:.0f},60" fill="{col}" opacity="0.16">'
                     f'<animateTransform attributeName="transform" type="rotate" values="-25 {x:.0f} {GROUND};25 {x:.0f} {GROUND};-25 {x:.0f} {GROUND}" dur="{d:.1f}s" repeatCount="indefinite"/></polygon>')
    night_on = 'values="0;0;1;1;0" keyTimes="0;0.5;0.58;0.92;1"'
    return f'<g opacity="0"><animate attributeName="opacity" {night_on} {loop}/>{"".join(beams)}</g>' + confetti


def pascoa(W, H, loop, rnd, road):
    colors = [("#f778ba", "#ffd1e8"), ("#7ee787", "#d2ffd9"), ("#58a6ff", "#cfe6ff"), ("#ffd166", "#fff1c9"), ("#bc8cff", "#ecdcff")]
    eggs = []
    for k in range(12):
        x = 40 + k * (W - 80) / 11 + rnd() * 14
        a, b = colors[k % 5]
        eggs.append(f'<g transform="translate({x:.0f} {GROUND + 2}) rotate({(rnd() - 0.5) * 30:.0f})">'
                    f'<ellipse cx="0" cy="-6" rx="5.5" ry="7.5" fill="{a}"/>'
                    f'<path d="M-5 -6 L-2 -8 L1 -6 L4 -8 L5.5 -6" fill="none" stroke="{b}" stroke-width="1.3"/></g>')
    # coelho pulando pela calçada durante o dia
    hop = ";".join(f"0 {0 if k % 2 == 0 else -14}" for k in range(9))
    bunny = (f'<g><animateTransform attributeName="transform" type="translate" values="-40 {GROUND - 4};-40 {GROUND - 4};{W + 40} {GROUND - 4};{W + 40} {GROUND - 4}" keyTimes="0;0.05;0.45;1" {loop}/>'
             f'<g><animateTransform attributeName="transform" type="translate" values="{hop}" dur="2.4s" repeatCount="indefinite"/>'
             '<ellipse cx="0" cy="0" rx="10" ry="7" fill="#f0f6fc"/><circle cx="9" cy="-6" r="5" fill="#f0f6fc"/>'
             '<ellipse cx="8" cy="-15" rx="1.8" ry="6" fill="#f0f6fc"/><ellipse cx="11" cy="-15" rx="1.8" ry="6" fill="#f0f6fc"/>'
             '<ellipse cx="8" cy="-15" rx="0.8" ry="4" fill="#ffb3c8"/><circle cx="11" cy="-7" r="0.9" fill="#161b22"/>'
             '<circle cx="14" cy="-5" r="0.9" fill="#ff7b72"/><circle cx="-10" cy="-2" r="3" fill="#ffffff"/></g></g>')
    return "".join(eggs) + bunny


def junina(W, H, loop, rnd, road):
    colors = ["#ff7b72", "#ffd166", "#7ee787", "#58a6ff", "#f778ba"]
    flags = "".join(
        _garland(W, y0, 14, n, lambda x, y, k: f'<polygon points="{x - 5:.0f},{y:.0f} {x + 5:.0f},{y:.0f} {x + 5:.0f},{y + 11:.0f} {x:.0f},{y + 7:.0f} {x - 5:.0f},{y + 11:.0f}" fill="{colors[k % 5]}">'
                 f'<animateTransform attributeName="transform" type="rotate" values="-6 {x:.0f} {y:.0f};6 {x:.0f} {y:.0f};-6 {x:.0f} {y:.0f}" dur="{2 + (k % 3) * 0.4:.1f}s" repeatCount="indefinite"/></polygon>')
        for y0, n in ((58, 4), (96, 5)))
    fx = W - 120
    flames = "".join(f'<path d="M{dx - 8} 0 Q{dx - 6} -14 {dx} -{h} Q{dx + 6} -14 {dx + 8} 0 Z" fill="{c}">'
                     f'<animateTransform attributeName="transform" type="scale" values="1 1;1.08 0.85;0.95 1.1;1 1" dur="{d}s" repeatCount="indefinite"/></path>'
                     for dx, h, c, d in ((-6, 26, "#ff7b2e", 0.5), (6, 22, "#ff9e3d", 0.6), (0, 34, "#ffd166", 0.45), (0, 18, "#fff1c9", 0.35)))
    sparks = "".join(f'<circle cx="{(rnd() - 0.5) * 16:.0f}" cy="-20" r="1.2" fill="#ffd166">'
                     f'<animateTransform attributeName="transform" type="translate" values="0 0;{(rnd() - 0.5) * 30:.0f} -70" dur="{1.2 + rnd():.1f}s" begin="-{rnd() * 2:.1f}s" repeatCount="indefinite"/>'
                     f'<animate attributeName="opacity" values="1;0" dur="{1.2 + rnd():.1f}s" repeatCount="indefinite"/></circle>' for _ in range(10))
    fire = (f'<g transform="translate({fx} {GROUND + 4})">'
            '<ellipse cx="0" cy="-10" rx="60" ry="34" fill="#ff9e3d" opacity="0.12"/>'
            '<path d="M-18 0 L14 -8 M-14 -8 L18 0" stroke="#8b5a2b" stroke-width="4" stroke-linecap="round"/>'
            f'<g>{flames}</g>{sparks}</g>')
    return flags + fire


LAYERS = {"natal": natal, "anonovo": anonovo, "halloween": halloween, "carnaval": carnaval, "pascoa": pascoa, "junina": junina}
