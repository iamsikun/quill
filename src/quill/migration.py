from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .manifest import InstallManifest
from .sync import MANIFEST_PATH, MARKER_END, MARKER_START, hash_file, safe_path

_ROLES = ('literature-reviewer', 'paper-outliner', 'intro-writer', 'technical-writer',
          'empirics-writer', 'citation-manager', 'latex-assembler', 'venue-formatter',
          'peer-reviewer', 'revision-planner', 'copyeditor')
_WORKFLOWS = ('new-paper', 'import-paper', 'literature-search', 'draft-paper',
              'draft-section', 'edit-section', 'review-paper', 'revise-paper',
              'set-target', 'create-journal-version', 'assemble', 'polish', 'camera-ready')
LEGACY_FILES = frozenset(
    [f'{prefix}/{slug}.md' for prefix in ('.claude/agents', '.pepper/adapters/codex/roles') for slug in _ROLES]
    + [f'{prefix}/{slug}.md' for prefix in ('.claude/commands', '.pepper/adapters/codex/workflows') for slug in _WORKFLOWS]
    + ['.claude/settings.json', '.pepper/writing-style.md', '.pepper/shared-agent-protocols.md']
)


@dataclass
class MigrationResult:
    removed_files: list[str] = field(default_factory=list)
    updated_files: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)


def _without_marker_block(content: bytes) -> bytes:
    """Remove only complete marker lines and their contents; preserve outside bytes."""
    lines = content.splitlines(keepends=True)
    starts = [i for i, line in enumerate(lines) if line.strip() == MARKER_START.encode()]
    ends = [i for i, line in enumerate(lines) if line.strip() == MARKER_END.encode()]
    if not starts and not ends:
        return content
    if len(starts) != 1 or len(ends) != 1 or starts[0] >= ends[0]:
        raise ValueError('ambiguous Pepper instruction markers; resolve manually')
    return b''.join(lines[:starts[0]] + lines[ends[0] + 1:])


def migrate_project(repo_root: Path, *, dry_run: bool = False) -> MigrationResult:
    manifest_path = safe_path(repo_root, MANIFEST_PATH.as_posix())
    manifest = InstallManifest.load(manifest_path)
    owned = set(manifest.managed_files) if manifest else set()
    result = MigrationResult()
    retired: set[str] = set()
    deletions: list[Path] = []
    updates: list[tuple[Path, bytes]] = []
    for relative in sorted(LEGACY_FILES):
        try:
            path = safe_path(repo_root, relative)
            if not path.exists():
                if relative in owned:
                    retired.add(relative)
                continue
            if relative not in owned:
                # An ordinary user settings file is not evidence of a Pepper install.
                if relative == '.claude/settings.json' and path.is_file() and b'PAPER_SYSTEM_VERSION' not in path.read_bytes():
                    continue
                result.conflicts.append(f'{relative}: no manifest ownership; left unchanged')
            elif not path.is_file() or hash_file(path) != manifest.hashes.get(relative):
                result.conflicts.append(f'{relative}: locally modified; left unchanged')
            else:
                result.removed_files.append(relative)
                retired.add(relative)
                deletions.append(path)
        except ValueError as exc:
            result.conflicts.append(str(exc))
    for relative in ('AGENTS.md', 'CLAUDE.md'):
        try:
            path = safe_path(repo_root, relative)
            if not path.exists():
                continue
            content = path.read_bytes()
            updated = _without_marker_block(content)
            if updated != content:
                result.updated_files.append(relative)
                updates.append((path, updated))
        except ValueError as exc:
            result.conflicts.append(f'{relative}: {exc}')
    if manifest and retired:
        result.updated_files.append(MANIFEST_PATH.as_posix())
    if dry_run:
        return result
    for path in deletions:
        path.unlink()
    for path, updated in updates:
        if updated:
            path.write_bytes(updated)
        else:
            path.unlink()
    if manifest and retired:
        manifest.managed_files = [p for p in manifest.managed_files if p not in retired]
        manifest.hashes = {p: digest for p, digest in manifest.hashes.items() if p not in retired}
        manifest.managed_files_by_scope = {
            scope: [p for p in paths if p not in retired]
            for scope, paths in manifest.managed_files_by_scope.items()
        }
        manifest.save(manifest_path)
    return result
