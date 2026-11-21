"""Versão em texto do README em imagens (para buscadores, leitores de tela e quem bloqueia imagens).

Lê os mesmos textos das imagens em scripts/readme-sections.html, então as duas versões não
se desencontram. Fica num <details> recolhido no fim do README: visível para quem abrir,
legível para o buscador, sem esconder nada (texto escondido só para SEO é penalizado).
"""
from html.parser import HTMLParser
from pathlib import Path

from build_brand import TEXT

SECTIONS = Path(__file__).resolve().parent / "readme-sections.html"
BLOCKS = {"kicker", "h2", "p", "li", "title", "sub", "pn", "pa", "pd", "tag"}


class Sections(HTMLParser):
    """Junta, por peça (data-shot), os blocos de texto na ordem: [(classe, texto), ...]."""

    def __init__(self):
        super().__init__()
        self.shots, self.shot, self.stack, self.buf = {}, None, [], None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "data-shot" in a:
            self.shot = a["data-shot"]
            self.shots[self.shot] = []
        kind = next((c for c in (a.get("class") or "").split() if c in BLOCKS), None) or (tag if tag in BLOCKS else None)
        if self.shot and kind and self.buf is None:
            self.buf, self.kind, self.depth = [], kind, 0
        if self.buf is not None:
            self.depth += 1
            if tag == "b":
                self.buf.append("**")
            elif kind == "pa":  # área do projeto, dentro do nome
                self.buf.append(" · ")

    def handle_endtag(self, tag):
        if self.buf is None:
            return
        if tag == "b":
            self.buf.append("**")
        self.depth -= 1
        if self.depth == 0:
            text = " ".join("".join(self.buf).split()).strip()
            if text:
                self.shots[self.shot].append((self.kind, text))
            self.buf = None

    def handle_data(self, data):
        if self.buf is not None:
            self.buf.append(data)


def parse():
    p = Sections()
    p.feed(SECTIONS.read_text(encoding="utf-8"))
    return p.shots


def heading(kicker):
    """"02 / ESTUDOS DE CASO" -> "02 / Estudos de caso"."""
    num, _, rest = kicker.partition(" / ")
    return f"{num} / {rest.capitalize()}"


def area_name(a):
    return a if len(a) <= 3 else a.capitalize()


def first(shot, kind):
    return next(t for k, t in shot if k == kind)


def all_of(shot, kind):
    return [t for k, t in shot if k == kind]


def markdown(projects, case_links, li, mail):
    """projects: [(shot, url)], case_links: {shot: url}."""
    s = parse()
    out = ["## Rafael Tanimoto — Desenvolvedor Backend Java, Spring Boot e Android", ""]
    out += ["São Paulo, Brasil · remoto ou híbrido · inglês fluente · aberto a oportunidades", ""]
    out += [f"[LinkedIn]({li}) · [Email]({mail})", ""]

    about = s["about"]
    out += [f"### {heading(first(about, 'kicker'))}", ""] + [p + "\n" for p in all_of(about, "p")]

    out += [f"### {heading(first(s['cases-title'], 'kicker'))}", ""]
    for shot, url in case_links.items():
        c = s[shot]
        out += [f"#### [{first(c, 'title')}]({url})", f"*{first(c, 'sub')}*", ""] + [p + "\n" for p in all_of(c, "p")]

    out += [f"### {heading(first(s['projects-title'], 'kicker'))}", "", "| Projeto | Área | Entrega |", "|---|---|---|"]
    for shot, url in projects:
        name, area = first(s[shot], "pn").split(" · ")
        out.append(f"| [{name}]({url}) | {area_name(area)} | {first(s[shot], 'pd')} |")
    out.append("")

    out += ["### 04 / Stack", ""] + [f"- **{group}:** {', '.join(items)}" for group, items in TEXT["pt"]["stack"]] + [""]

    edu = s["education"]
    out += [f"### {heading(first(edu, 'kicker'))}", ""] + [f"- {li_}" for li_ in all_of(edu, "li")] + [""]

    contact = s["contact"]
    out += [f"### {heading(first(contact, 'kicker'))}", "", all_of(contact, "p")[0].replace(
        "LinkedIn", f"[LinkedIn]({li})", 1).replace("email", f"[email]({mail})", 1), ""]

    body = "\n".join(out).replace("\n\n\n", "\n\n").strip()
    return ("\n<details>\n<summary><b>Versão em texto</b> (mesmo conteúdo das imagens)</summary>\n\n"
            + body + "\n\n</details>\n")
