"""Opt-in Claude Code hooks that make the writing review hard to skip.

`post-edit` runs after an Edit or Write of a manuscript file. It remembers the file
as awaiting review and returns `quill check` candidates to the agent as context.
`stop` blocks the agent from finishing once while an edited manuscript file lacks a
current review record. Both read the hook's JSON from stdin and never fail the host.
"""
from __future__ import annotations

import json
from pathlib import Path

from .check import check_file, format_result
from .review import ReviewStore

MANUSCRIPT = {'.tex', '.md', '.markdown', '.qmd', '.rmd', '.txt'}
SKIP_PARTS = {'.claude', '.agents', '.quill', '.git', 'node_modules', 'build'}
REMINDER = ('Quill review: before finishing, review the edited manuscript text with the Quill '
            'skill\'s references/review.md and references/checklist.md, repair only flagged spans, '
            'then run `quill review record {files}`. Keep the review out of the manuscript and the reply.')


def is_manuscript(path: Path, project: Path) -> bool:
    try:
        relative = path.resolve().relative_to(project)
    except ValueError:
        return False
    names = {part.lower() for part in relative.parts[:-1]}
    return (path.suffix.lower() in MANUSCRIPT and not names & SKIP_PARTS
            and relative.name.lower() not in {'readme.md', 'changelog.md', 'agents.md', 'claude.md'})


def pending_path(store: ReviewStore) -> Path:
    return store.path / 'pending.json'


def load_pending(store: ReviewStore) -> list[str]:
    path = pending_path(store)
    return json.loads(path.read_text()) if path.is_file() else []


def post_edit(event: dict) -> dict | None:
    file = (event.get('tool_input') or {}).get('file_path')
    project = Path(event.get('cwd') or '.').resolve()
    if not file:
        return None
    path = Path(file)
    path = path if path.is_absolute() else project / path
    if not path.is_file() or not is_manuscript(path, project):
        return None
    store = ReviewStore.for_project(path.parent)
    relative = store.relative(path)
    pending = load_pending(store)
    if relative not in pending:
        store.path.mkdir(parents=True, exist_ok=True)
        ignore = store.path / '.gitignore'
        if not ignore.exists():
            ignore.write_text('*\n')
        pending_path(store).write_text(json.dumps(pending + [relative]) + '\n')
    result = check_file(path)
    context = REMINDER.format(files=relative)
    if result['style']:
        context += '\n' + format_result({**result, 'file': relative}).rstrip()
    return {'hookSpecificOutput': {'hookEventName': 'PostToolUse', 'additionalContext': context}}


def stop(event: dict) -> dict | None:
    if event.get('stop_hook_active'):
        return None  # block at most once per stop attempt
    project = Path(event.get('cwd') or '.').resolve()
    store = ReviewStore.for_project(project)
    pending = [p for p in load_pending(store) if (store.project / p).is_file()]
    stale = [p for p, info in store.status([store.project / p for p in pending]).items()
             if info['state'] != 'current'] if pending else []
    if not stale:
        return None
    return {'decision': 'block', 'reason': REMINDER.format(files=' '.join(stale))
            + ' If the edit was only a copyedit, a brief self-check suffices before recording it.'}


def run(action: str, payload: str) -> str:
    try:
        event = json.loads(payload or '{}')
        result = post_edit(event) if action == 'post-edit' else stop(event)
    except (OSError, ValueError, KeyError, TypeError):
        return ''  # a hook must never break the host session
    return json.dumps(result) if result else ''
