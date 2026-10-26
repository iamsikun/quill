"""Render paper.md to build/paper.html with the standard library only."""
import html
import re
from pathlib import Path

lines = Path('paper.md').read_text().splitlines()
out, table = [], []


def flush():
    if not table:
        return
    rows = [r for r in table if not re.fullmatch(r'\|?[\s:|-]+\|?', r)]
    spec = next((r for r in table if re.fullmatch(r'\|?[\s:|-]+\|?', r)), '')
    aligns = [('center' if c.strip().startswith(':') and c.strip().endswith(':') else
               'right' if c.strip().endswith(':') else 'left') for c in spec.strip('|').split('|')]
    out.append('<table>')
    for i, row in enumerate(rows):
        cells = [c.strip() for c in row.strip('|').split('|')]
        tag = 'th' if i == 0 else 'td'
        out.append('<tr>' + ''.join(
            f'<{tag} style="text-align:{aligns[j] if j < len(aligns) else "left"}">{html.escape(c)}</{tag}>'
            for j, c in enumerate(cells)) + '</tr>')
    out.append('</table>')
    table.clear()


for line in lines:
    if line.startswith('|'):
        table.append(line)
        continue
    flush()
    if line.startswith('#'):
        level = len(line) - len(line.lstrip('#'))
        out.append(f'<h{level}>{html.escape(line[level:].strip())}</h{level}>')
    elif line.strip():
        out.append(f'<p>{html.escape(line)}</p>')
flush()
Path('build').mkdir(exist_ok=True)
Path('build/paper.html').write_text('<!doctype html>\n<meta charset="utf-8">\n' + '\n'.join(out) + '\n')
print('wrote build/paper.html')
