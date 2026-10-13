"""Deterministic helpers for personal writing memory.

The memory itself is plain Markdown that the agent reads and edits. This module only
keeps Quill's last version of each file it wrote and reports what changed since.
"""
from __future__ import annotations

from collections import Counter
import difflib
import os
from pathlib import Path
import re
import tempfile

from .sync import find_repo_root

PARAGRAPH_BREAK = re.compile(r'\r?\n[ \t]*(?:\r?\n[ \t]*)+')
BEGIN = re.compile(r'\\begin\{[^}]*\}')
END = re.compile(r'\\end\{[^}]*\}')
# Changes to these are usually corrections of substance, not of style.
TOUCHES = {
    'math': re.compile(r'\$\$.*?\$\$|\$[^$]+\$|\\\[.*?\\\]|\\\(.*?\\\)'
                       r'|\\begin\{(equation|align|gather|multline|eqnarray)\*?\}.*?\\end\{\1\*?\}', re.S),
    'citation': re.compile(r'\\(?:no)?cite[a-zA-Z]*\*?(?:\[[^\]]*\])*\{[^}]*\}'),
    'reference': re.compile(r'\\(?:ref|eqref|cref|Cref|autoref|pageref|label)\{[^}]*\}'),
    'number': re.compile(r'(?<![A-Za-z\\])\d+(?:[.,]\d+)*%?'),
}


def default_store(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / '.quill/style').is_dir():
            return candidate / '.quill/style'
    return find_repo_root(current) / '.quill/style'


def atomic_write(path: Path, data: bytes) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix='.write-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(data)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def paragraph_spans(text: str) -> list[list[int]]:
    """Exact paragraph spans; blank lines inside a LaTeX environment do not split it."""
    spans, position = [], 0
    for match in PARAGRAPH_BREAK.finditer(text):
        if text[position:match.start()].strip():
            spans.append([position, match.start()])
        position = match.end()
    if text[position:].strip():
        spans.append([position, len(text)])
    merged, depth = [], 0
    for start, end in spans:
        if depth > 0 and merged:
            merged[-1][1] = end
        else:
            merged.append([start, end])
        chunk = text[start:end]
        depth = max(0, depth + len(BEGIN.findall(chunk)) - len(END.findall(chunk)))
    return merged


def touches(before: str, after: str) -> list[str]:
    return [name for name, pattern in TOUCHES.items()
            if Counter(m.group(0) for m in pattern.finditer(before))
            != Counter(m.group(0) for m in pattern.finditer(after))]


def similar(left: str, right: str) -> bool:
    matcher = difflib.SequenceMatcher(None, left, right, autojunk=False)
    return matcher.quick_ratio() >= 0.9 and matcher.ratio() >= 0.9


def align_block(old: list[str], new: list[str], i1: int, i2: int, j1: int, j2: int) -> list[tuple]:
    """Pair edited paragraphs separately; keep a split or merged paragraph with its source."""
    if i2 - i1 == j2 - j1:
        return [(i1 + k, i1 + k + 1, j1 + k, j1 + k + 1) for k in range(i2 - i1)]
    def score(p, q):
        left = '\n\n'.join(s.strip() for s in old[i:i + p])
        right = '\n\n'.join(s.strip() for s in new[j:j + q])
        return difflib.SequenceMatcher(None, left, right, autojunk=False).ratio()
    groups, i, j = [], i1, j1
    while i < i2 and j < j2:
        shapes = [(p, q) for p, q in ((1, 1), (1, 2), (1, 3), (2, 1), (3, 1)) if i + p <= i2 and j + q <= j2]
        best, (p, q) = max((score(p, q), (p, q)) for p, q in shapes)
        if best < 0.5:
            p, q = 1, 1
        groups.append((i, i + p, j, j + q))
        i, j = i + p, j + q
    if i < i2 or j < j2:
        groups.append((i, i2, j, j2))
    return groups


def compare(before: str, after: str) -> list[dict]:
    """Paragraph-level changes from Quill's version to the current text, with exact bytes."""
    old_spans, new_spans = paragraph_spans(before), paragraph_spans(after)
    old = [before[s:e] for s, e in old_spans]
    new = [after[s:e] for s, e in new_spans]
    matcher = difflib.SequenceMatcher(None, [p.strip() for p in old], [p.strip() for p in new],
                                      autojunk=False)
    groups = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'replace':
            groups += align_block(old, new, i1, i2, j1, j2)
        elif tag != 'equal':
            groups.append((i1, i2, j1, j2))
    changes = []
    for i1, i2, j1, j2 in groups:
        changes.append({
            'paragraph': j1 + 1,
            'before': before[old_spans[i1][0]:old_spans[i2 - 1][1]] if i2 > i1 else '',
            'after': after[new_spans[j1][0]:new_spans[j2 - 1][1]] if j2 > j1 else '',
            'context': (old[i1 - 1] if i1 > 0 else '', old[i2] if i2 < len(old) else ''),
            'removed': old[i1:i2], 'added': new[j1:j2]})
    for change in changes:
        others = [c for c in changes if c is not change]
        pairs = [(p, q) for o in others for p in change['removed'] for q in o['added']]
        pairs += [(p, q) for o in others for p in change['added'] for q in o['removed']]
        change['moved'] = any(similar(p.strip(), q.strip()) for p, q in pairs)
        change['touches'] = touches(change['before'], change['after'])
    for change in changes:
        del change['removed'], change['added']
    return changes


class StyleStore:
    """Project memory folder: `profile.md`, `examples.md`, and `baselines/`."""

    def __init__(self, path: Path):
        self.path = Path(path).expanduser().resolve()
        self.project = self.path.parent.parent

    def relative(self, file: Path) -> str:
        path = Path(file).resolve()
        try:
            return path.relative_to(self.project).as_posix()
        except ValueError:
            raise ValueError(f'{file} is outside the project {self.project}') from None

    def baseline_path(self, relative: str) -> Path:
        return self.path / 'baselines' / relative

    def ensure(self) -> None:
        self.path.mkdir(parents=True, exist_ok=True)
        ignore = self.path / '.gitignore'
        if not ignore.exists():
            # Memory quotes unpublished manuscript text; keep it out of version control.
            ignore.write_text('*\n')

    def baseline(self, file: Path) -> str:
        """Record the current file as Quill's last version."""
        relative = self.relative(file)
        content = Path(file).read_bytes()
        content.decode('utf-8')
        self.ensure()
        target = self.baseline_path(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        atomic_write(target, content)
        return relative

    def tracked(self) -> list[str]:
        root = self.path / 'baselines'
        return sorted(p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()) if root.is_dir() else []

    def changes(self, files: list[Path] | None = None) -> dict[str, list[dict] | str]:
        """Changes since Quill's last version, per file. Read-only."""
        relatives = [self.relative(f) for f in files] if files else self.tracked()
        result = {}
        for relative in relatives:
            baseline = self.baseline_path(relative)
            current = self.project / relative
            if not baseline.is_file():
                result[relative] = 'no baseline'
            elif not current.is_file():
                result[relative] = 'file removed'
            else:
                found = compare(baseline.read_bytes().decode('utf-8'), current.read_bytes().decode('utf-8'))
                if found:
                    result[relative] = found
        return result


def format_changes(result: dict) -> str:
    if not result:
        return 'No changes since Quill last wrote these files.\n'
    lines = []
    for relative, found in result.items():
        if isinstance(found, str):
            lines.append(f'{relative}: {found}\n')
            continue
        lines.append(f'{relative}: {len(found)} change(s) since Quill last wrote it\n')
        for number, change in enumerate(found, 1):
            notes = ([f"changed {', '.join(change['touches'])}"] if change['touches'] else [])
            notes += ['moved'] if change['moved'] else []
            lines.append(f"[{number}] paragraph {change['paragraph']}" + (f" ({'; '.join(notes)})" if notes else ''))
            if change['context'][0]:
                lines.append('  preceded by: ' + change['context'][0].strip().splitlines()[0][:100])
            lines.append('  Quill:  ' + (change['before'].strip().replace('\n', '\n          ') or '(nothing)'))
            lines.append('  now:    ' + (change['after'].strip().replace('\n', '\n          ') or '(removed)'))
            lines.append('')
    return '\n'.join(lines).rstrip() + '\n'
