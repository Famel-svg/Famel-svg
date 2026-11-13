"""Generate the profile calendar from GitHub's public contribution HTML."""
import json
import re
from datetime import date, timedelta
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
COLORS = ['#161b22', '#0e4429', '#006d32', '#26a641', '#39d353']


class CalendarParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cells = {}
        self.counts = {}
        self.target = None
        self.label = ''

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'td' and 'data-date' in attrs:
            self.cells[attrs['id']] = (date.fromisoformat(attrs['data-date']), int(attrs['data-level']))
        if tag == 'tool-tip' and attrs.get('for', '').startswith('contribution-day-component-'):
            self.target = attrs['for']
            self.label = ''

    def handle_data(self, text):
        if self.target:
            self.label += text

    def handle_endtag(self, tag):
        if tag == 'tool-tip' and self.target:
            label = self.label.strip()
            match = re.match(r'([\d,]+) contributions? on ', label)
            if label.startswith('No contributions on '):
                self.counts[self.target] = 0
            elif match:
                self.counts[self.target] = int(match[1].replace(',', ''))
            else:
                raise ValueError(f'Unknown contribution label: {label}')
            self.target = None


def parse_calendar(html):
    parser = CalendarParser()
    parser.feed(html)
    if not parser.cells or parser.cells.keys() != parser.counts.keys():
        raise ValueError('Missing calendar cells or contribution counts')
    days = sorted((day, level, parser.counts[key]) for key, (day, level) in parser.cells.items())
    if len({day for day, _, _ in days}) != len(days):
        raise ValueError('Duplicate calendar dates')
    for index, (day, level, count) in enumerate(days):
        if not 0 <= level <= 4 or count < 0 or (level == 0) != (count == 0):
            raise ValueError('Invalid contribution level/count')
        if index and day != days[index - 1][0] + timedelta(days=1):
            raise ValueError('Incomplete calendar')
    return days


def render(days):
    first = days[0][0]
    start = first - timedelta(days=(first.weekday() + 1) % 7)
    total = sum(count for _, _, count in days)
    period = f'{first:%d/%m/%Y} — {days[-1][0]:%d/%m/%Y}'
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="960" height="250" viewBox="0 0 960 250" role="img" aria-labelledby="title desc">',
             '<title id="title">Contribuições de Famel-svg no GitHub</title>',
             f'<desc id="desc">{total} contribuições em {period}. Calendário atualizado diariamente.</desc>',
             '<rect x="1" y="1" width="958" height="248" rx="18" fill="#0d1117" stroke="#30363d"/>',
             '<g font-family="Consolas, monospace" font-size="16" fill="#8b949e">',
             '<text x="32" y="36" fill="#7ee787">$ ./contributions.sh</text>',
             f'<text x="32" y="222" fill="#e6edf3">{total} contribuições · {period}</text>',
             '<text x="727" y="222">Menos</text><text x="890" y="222">Mais</text></g>']
    month = None
    names = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    for day, level, count in days:
        week, row = divmod((day - start).days, 7)
        x, y = 40 + week * 16, 74 + row * 16
        if day.month != month:
            parts.append(f'<text x="{x}" y="62" fill="#8b949e" font-family="Consolas, monospace" font-size="12">{names[day.month - 1]}</text>')
            month = day.month
        label = escape(f'{day.isoformat()}: {count} contribuições')
        parts.append(f'<rect x="{x}" y="{y}" width="12" height="12" rx="3" fill="{COLORS[level]}"><title>{label}</title><animate attributeName="opacity" values="0.15;1" dur="0.35s" begin="{week * 0.018:.3f}s" fill="freeze"/></rect>')
    for index, color in enumerate(COLORS):
        parts.append(f'<rect x="{787 + index * 18}" y="211" width="12" height="12" rx="3" fill="{color}"/>')
    return '\n'.join(parts + ['</svg>']) + '\n'


def main():
    request = Request('https://github.com/users/Famel-svg/contributions', headers={'User-Agent': 'Famel-svg-profile', 'Accept-Language': 'en-US'})
    with urlopen(request, timeout=30) as response:
        days = parse_calendar(response.read().decode('utf-8'))
    if not 365 <= len(days) <= 371:
        raise ValueError(f'Unexpected calendar length: {len(days)}')
    svg = render(days)
    data = json.dumps([{'date': day.isoformat(), 'level': level, 'count': count} for day, level, count in days], indent=2) + '\n'
    (ROOT / 'data').mkdir(exist_ok=True)
    (ROOT / 'data/contributions.json').write_text(data, encoding='utf-8')
    (ROOT / 'assets/contributions.svg').write_text(svg, encoding='utf-8')
    print(f'Generated {len(days)} days, {sum(count for _, _, count in days)} contributions')


if __name__ == '__main__':
    main()
