"""Deterministic candidates for the writing review.

`quill check` reports two groups. Style candidates are spans that often signal a
problem the review checklist names: defensive contrasts, stock scaffolding,
workflow narration, code identifiers, leftover markers, and the author's own lint
patterns. Fidelity guards compare a file with an earlier version and report changed
numbers, citations, references, and mathematics, and edits outside an authorized
span. Every hit is a candidate for the model to judge; counts are not a score.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import os
from pathlib import Path
import re

import yaml

from .style import TOUCHES, compare, paragraph_spans


@dataclass(frozen=True)
class Pattern:
    rule: str
    name: str
    regex: re.Pattern
    raw: bool = False  # match comments and markers too, not only reader-facing prose


def _p(rule: str, name: str, regex: str, flags: int = re.I, raw: bool = False) -> Pattern:
    return Pattern(rule, name, re.compile(regex, flags), raw)


PATTERNS = [
    _p('E1', 'defensive contrast', r'\bNOT\b', 0),
    _p('E1', 'defensive contrast', r',\s+not\s+(?:a |an |the )?[A-Za-z][\w-]*'),
    _p('E1', 'denial of an alternative',
       r'\bnot to be confused with\b|\b(?:is|are) unrelated to\b|\bwe do not claim\b'
       r'|\bthis does not mean\b|\bthe paper does not (?:report|claim|address)\b'),
    _p('E2', 'generic wrap-up',
       r'\b(?:taken together|together, these|overall, (?:these|our)|in summary|in conclusion)\b'
       r'|\bshed(?:s|ding)? (?:new )?light on\b|\bpav(?:e|es|ing) the way\b'
       r'|\bplays? an? (?:crucial|key|pivotal|central|vital) role\b'),
    _p('E3', 'scaffolding',
       r'\b(?:importantly|crucially|notably|interestingly)\b,?'
       r'|\bit (?:is|should be) (?:worth noting|noted|emphasized)\b'
       r'|\bthis (?:highlights|underscores|demonstrates|illustrates) (?:the|that|how)\b'),
    _p('U5', 'commit or hash', r'\b(?=[0-9a-f]*[a-f])(?=[0-9a-f]*\d)[0-9a-f]{7,40}\b', 0),
    _p('U5', 'workflow narration',
       r'\b(?:worktree|working tree|uncommitted|dirty (?:tree|checkout)|local (?:snapshot|copy|checkout)'
       r'|this (?:session|workspace|repository)|the agent)\b'),
    _p('U5', 'code file or call',
       r'(?<![\w/])[\w./\\-]*\w\.(?:jsonl?|csv|tsv|py|ipynb|npz|npy|pkl|parquet|ya?ml|toml|sh)\b'
       r'|\b(?:np|numpy|pd|pandas|torch|scipy|sklearn|plt)\.[a-z_]\w*'
       r'|\\path\{|\b(?:reproducibility|artifact) record\b'),
    _p('U5', 'repair announcement',
       r'\b(?:now (?:shows?|displays?|uses?|correctly)|no longer (?:truncat|clip|overlap)\w*'
       r'|(?:was|were|has been|have been) (?:fixed|corrected|regenerated|repaired)'
       r'|without truncation|(?:use|uses|from) the same (?:results|data|runs|numbers))\b'),
    _p('E6', 'code identifier', r'(?<![\\\w])[A-Za-z][A-Za-z0-9]*(?:(?:\\_|_)[A-Za-z0-9]+)+\b', 0),
    _p('U5', 'placeholder or revision marker',
       r'\b(?:TODO|FIXME|XXX|TBD)\b|\\todo\b|\[(?:citation needed|cite|ref|TK)\]'
       r'|%\s*(?:REVISED|POLISHED|EDITED|CHANGED)\b|<!--\s*(?:TODO|REVISED|POLISHED)', 0, raw=True),
]

# Spans that are not reader-facing prose: math, commands whose arguments are keys
# or paths, comments, and code blocks. They are blanked so line numbers stay exact.
LATEX_COMMENT = re.compile(r'(?<!\\)%.*')
MASKS = [
    re.compile(r'```.*?```', re.S),
    re.compile(r'\\begin\{(verbatim|lstlisting|minted|equation|align|gather|multline|eqnarray|math'
               r'|displaymath)\*?\}.*?\\end\{\1\*?\}', re.S),
    re.compile(r'\$\$.*?\$\$|(?<!\\)\$[^$]+\$|\\\[.*?\\\]|\\\(.*?\\\)', re.S),
    re.compile(r'\\(?:(?:no)?cite[a-zA-Z]*\*?|ref|eqref|cref|Cref|autoref|pageref|label|url|href'
               r'|input|include|includegraphics|bibliography|bibliographystyle|usepackage'
               r'|documentclass|begin|end)(?:\[[^\]]*\])*\{[^}]*\}'),
]


def is_latex(file: Path, text: str) -> bool:
    return Path(file).suffix in ('.tex', '.ltx') or bool(re.search(r'\\(?:begin|section|documentclass)\b', text))


def mask(text: str, latex: bool = True) -> str:
    chars = list(text)
    for pattern in ([LATEX_COMMENT] if latex else []) + MASKS:
        for match in pattern.finditer(text):
            for index in range(match.start(), match.end()):
                if chars[index] != '\n':
                    chars[index] = ' '
    return ''.join(chars)


def profile_patterns(project: Path) -> tuple[list[Pattern], list[str]]:
    """Lint patterns from the shared and project profiles' `checks` headers."""
    config = Path(os.environ.get('XDG_CONFIG_HOME') or Path.home() / '.config')
    patterns, problems = [], []
    for path in (config / 'quill/profile.md', project / '.quill/style/profile.md'):
        if not path.is_file():
            continue
        text = path.read_text()
        if not text.startswith('---\n') or '\n---' not in text[4:]:
            continue
        try:
            header = yaml.safe_load(text[4:text.index('\n---', 4)]) or {}
        except yaml.YAMLError as exc:
            problems.append(f'{path}: unreadable header ({exc})')
            continue
        for entry in header.get('checks') or []:
            try:
                regex = re.compile(entry['pattern'])
            except (TypeError, KeyError, re.error) as exc:
                problems.append(f'{path}: skipped check {entry!r} ({exc})')
                continue
            patterns.append(Pattern('U7', f"profile: {entry.get('lesson', entry['pattern'])}", regex))
    return patterns, problems


def line_of(text: str, offset: int) -> int:
    return text.count('\n', 0, offset) + 1


def style_candidates(text: str, extra: list[Pattern] = (), latex: bool = True) -> list[dict]:
    prose = mask(text, latex)
    found = []
    for pattern in [*PATTERNS, *extra]:
        source = text if pattern.raw else prose
        for match in pattern.regex.finditer(source):
            if not match.group(0).strip():
                continue
            line = line_of(text, match.start())
            found.append({'line': line, 'rule': pattern.rule, 'name': pattern.name,
                          'match': match.group(0).strip(), 'text': text.splitlines()[line - 1].strip()})
    found.sort(key=lambda hit: (hit['line'], hit['rule']))
    return found


def parse_lines(spans: list[str]) -> list[tuple[int, int]]:
    result = []
    for span in spans:
        start, _, end = span.partition('-')
        first, last = int(start), int(end or start)
        if first < 1 or last < first:
            raise ValueError(f'invalid line span: {span}')
        result.append((first, last))
    return result


def keyless(text: str, name: str) -> str:
    """Digits inside citation keys and labels are not numbers in the text."""
    if name != 'number':
        return text
    return TOUCHES['reference'].sub(' ', TOUCHES['citation'].sub(' ', text))


def fidelity_guards(before: str, after: str, allowed: list[tuple[int, int]] = ()) -> list[dict]:
    spans = paragraph_spans(after)
    guards = []
    for change in compare(before, after):
        index = change['paragraph'] - 1
        if change['after'] and index < len(spans):
            first, last = line_of(after, spans[index][0]), line_of(after, spans[index][1] - 1)
        else:  # a deletion: report where the removed text used to be
            offset = spans[index][0] if index < len(spans) else len(after)
            first = last = line_of(after, offset)
        entry = {'paragraph': change['paragraph'], 'lines': [first, last], 'changes': {}}
        for name in change['touches']:
            old, new = (Counter(m.group(0) for m in TOUCHES[name].finditer(keyless(side, name)))
                        for side in (change['before'], change['after']))
            if old != new:
                entry['changes'][name] = {'removed': sorted((old - new).elements()),
                                          'added': sorted((new - old).elements())}
        if allowed and not any(first <= stop and last >= start for start, stop in allowed):
            entry['outside_span'] = True
        if entry['changes'] or entry.get('outside_span'):
            guards.append(entry)
    return guards


def check_file(file: Path, against: Path | None = None, lines: list[str] = (),
               profile: bool = True, project: Path | None = None) -> dict:
    text = Path(file).read_bytes().decode('utf-8')
    extra, problems = profile_patterns(project or Path(file).resolve().parent) if profile else ([], [])
    result = {'file': str(file), 'style': style_candidates(text, extra, is_latex(file, text)),
              'problems': problems}
    if against is not None:
        before = Path(against).read_bytes().decode('utf-8')
        result['fidelity'] = fidelity_guards(before, text, parse_lines(lines))
    elif lines:
        raise ValueError('--lines needs --against or --baseline to compare with')
    return result


def format_result(result: dict) -> str:
    out = []
    style, guards = result['style'], result.get('fidelity')
    out.append(f"{result['file']}: {len(style)} style candidate(s)"
               + (f", {len(guards)} fidelity guard(s)" if guards is not None else ''))
    if style:
        out.append('Style candidates (judge each in context; see the checklist rule):')
        for hit in style:
            out.append(f"  {hit['line']}: {hit['rule']} {hit['name']}: {hit['match']!r}")
            out.append(f"      {hit['text'][:160]}")
    if guards:
        out.append('Fidelity guards (recheck each changed span against the sources):')
        for guard in guards:
            first, last = guard['lines']
            where = f"lines {first}-{last}" if last > first else f"line {first}"
            notes = [f"{name}: -{', '.join(c['removed']) or '∅'} +{', '.join(c['added']) or '∅'}"
                     for name, c in guard['changes'].items()]
            if guard.get('outside_span'):
                notes.append('outside the authorized lines')
            out.append(f"  paragraph {guard['paragraph']} ({where}): " + '; '.join(notes))
    out.extend(f'warning: {problem}' for problem in result['problems'])
    return '\n'.join(out) + '\n'
