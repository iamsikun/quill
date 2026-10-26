"""Review records: which version of a manuscript file last passed the writing review.

Records live in the project's `.quill/reviews/`, which Git ignores. Each holds the
SHA-256 of the reviewed bytes, so any later edit makes the review stale.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from . import __version__
from .style import atomic_write, default_store


class ReviewStore:
    def __init__(self, path: Path):
        self.path = Path(path).expanduser().resolve()
        self.project = self.path.parent.parent

    @classmethod
    def for_project(cls, start: Path | None = None) -> 'ReviewStore':
        return cls(default_store(start).parent / 'reviews')

    def relative(self, file: Path) -> str:
        try:
            return Path(file).resolve().relative_to(self.project).as_posix()
        except ValueError:
            raise ValueError(f'{file} is outside the project {self.project}') from None

    def record_path(self, relative: str) -> Path:
        return self.path / f'{relative}.json'

    def record(self, file: Path, summary: str = '', findings: str = '') -> str:
        relative = self.relative(file)
        digest = hashlib.sha256(Path(file).read_bytes()).hexdigest()
        self.path.mkdir(parents=True, exist_ok=True)
        ignore = self.path / '.gitignore'
        if not ignore.exists():
            ignore.write_text('*\n')
        target = self.record_path(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        history = json.loads(target.read_text()).get('history', []) if target.is_file() else []
        entry = {'sha256': digest, 'recorded_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
                 'quill_version': __version__, 'summary': summary, 'findings': findings}
        history.append(entry)
        atomic_write(target, (json.dumps({'file': relative, **entry, 'history': history}, indent=2) + '\n').encode())
        return relative

    def recorded(self) -> list[str]:
        if not self.path.is_dir():
            return []
        return sorted(p.relative_to(self.path).as_posix()[:-5] for p in self.path.rglob('*.json')
                      if p != self.path / 'pending.json')

    def status(self, files: list[Path] | None = None) -> dict[str, dict]:
        relatives = [self.relative(f) for f in files] if files else self.recorded()
        result = {}
        for relative in relatives:
            record, current = self.record_path(relative), self.project / relative
            if not current.is_file():
                result[relative] = {'state': 'file removed'}
            elif not record.is_file():
                result[relative] = {'state': 'no review'}
            else:
                data = json.loads(record.read_text())
                fresh = hashlib.sha256(current.read_bytes()).hexdigest() == data['sha256']
                result[relative] = {'state': 'current' if fresh else 'stale',
                                    'recorded_at': data['recorded_at']}
        return result


def format_status(result: dict[str, dict]) -> str:
    if not result:
        return 'No review records.\n'
    lines = []
    for relative, info in result.items():
        state = info['state']
        if state == 'current':
            lines.append(f"{relative}: current (reviewed {info['recorded_at']})")
        elif state == 'stale':
            lines.append(f"{relative}: stale (changed since the review on {info['recorded_at']})")
        else:
            lines.append(f'{relative}: {state}')
    return '\n'.join(lines) + '\n'
