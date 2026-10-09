from __future__ import annotations

import json
import difflib
import os
from importlib.resources import files
from pathlib import Path

from .sync import SyncResult, hash_bytes, hash_file, package_version, resource_bytes, safe_path

SKILL_MANIFEST = '.quill-install.json'
HOSTS = ('codex', 'claude')


def skill_bytes() -> dict[str, bytes]:
    """The wheel embeds the canonical folder; editable installs read it in place."""
    packaged = files('quill').joinpath('skill')
    if packaged.is_dir():
        return resource_bytes(packaged)
    source = Path(__file__).resolve().parents[2] / 'skills/quill'
    if not (source / 'SKILL.md').is_file():
        raise FileNotFoundError('Quill skill resources are missing; reinstall the package')
    return resource_bytes(source)


def skill_destinations(repo_root: Path, *, host: str, scope: str) -> dict[str, Path]:
    """Codex reads .agents/skills at both scopes; Claude Code reads .claude/skills."""
    if host not in (*HOSTS, 'all') or scope not in ('user', 'project'):
        raise ValueError('host must be codex, claude, or all; scope must be user or project')
    selected = HOSTS if host == 'all' else (host,)
    root = repo_root.resolve() if scope == 'project' else Path.home().resolve()
    bases = {name: safe_path(root, f'{directory}/skills')
             for name, directory in (('codex', '.agents'), ('claude', '.claude'))
             if name in selected}
    for base in bases.values():
        if (base / 'quill').is_symlink():
            raise ValueError(f'{base / "quill"} is a symlink, probably from install.sh; '
                             'manage it with install.sh update/uninstall instead')
    return {name: safe_path(bases[name], 'quill') for name in selected}


def legacy_codex_destination(*, host: str, scope: str) -> Path | None:
    """Quill 0.2 copied the user-level Codex skill into $CODEX_HOME/skills, which Codex no longer reads."""
    if scope != 'user' or host not in ('codex', 'all'):
        return None
    codex_home = Path(os.environ.get('CODEX_HOME') or Path.home() / '.codex').expanduser().resolve()
    legacy = codex_home / 'skills/quill'
    if legacy.is_symlink() or not (legacy / SKILL_MANIFEST).is_file():
        return None
    return legacy


def _load_manifest(path: Path) -> dict | None:
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict) or data.get('schema_version') != 1 or not isinstance(data.get('hashes'), dict):
        raise ValueError(f'invalid skill ownership manifest: {path}')
    for relative, digest in data['hashes'].items():
        if not isinstance(relative, str) or not isinstance(digest, str) or len(digest) != 64:
            raise ValueError(f'invalid skill checksum in {path}')
        safe_path(path.parent, relative)
        if relative == SKILL_MANIFEST:
            raise ValueError(f'manifest cannot own itself: {path}')
    return data


def _preview(result: SyncResult, path: Path, payload: bytes | None, *, diff: bool) -> None:
    action = 'delete' if payload is None else ('update' if path.exists() else 'create')
    result.planned_changes.append(f'{action}: {path}')
    if diff and path.name != SKILL_MANIFEST:
        before = path.read_bytes() if path.is_file() else b''
        after = payload or b''
        try:
            result.diffs.append(''.join(difflib.unified_diff(
                before.decode().splitlines(keepends=True), after.decode().splitlines(keepends=True),
                fromfile=f'{path} (current)', tofile=f'{path} (proposed)')))
        except UnicodeDecodeError:
            result.diffs.append(f'{path}: binary content differs\n')


def install_skill(repo_root: Path, *, host: str = 'all', scope: str = 'user', sync: bool = False,
                  dry_run: bool = False, diff: bool = False) -> SyncResult:
    """Preflight all selected hosts before updating any files. Never force edits away."""
    assets = skill_bytes()
    if 'SKILL.md' not in assets:
        raise ValueError('Quill skill bundle has no SKILL.md')
    hashes = {relative: hash_bytes(payload) for relative, payload in assets.items()}
    result = SyncResult()
    legacy = legacy_codex_destination(host=host, scope=scope)
    if legacy is not None:
        result.conflicts.append(f'{legacy}: older Quill copy that Codex no longer reads; '
                                'remove it with quill skill uninstall --host codex --scope user')
        return result
    writes: list[tuple[Path, bytes]] = []
    deletes: list[Path] = []
    for name, root in skill_destinations(repo_root, host=host, scope=scope).items():
        manifest_path = safe_path(root, SKILL_MANIFEST)
        manifest = _load_manifest(manifest_path)
        if sync and manifest is None:
            result.conflicts.append(f'{root}: not managed by Quill; run quill skill install first')
            continue
        known = manifest['hashes'] if manifest else {}
        for relative, payload in assets.items():
            destination = safe_path(root, relative)
            if destination.exists():
                if not destination.is_file():
                    result.conflicts.append(str(destination))
                    continue
                current = hash_file(destination)
                if current == hashes[relative]:
                    continue
                if current != known.get(relative):
                    _preview(result, destination, payload, diff=diff)
                    result.conflicts.append(f'{destination}: locally modified or not owned')
                    continue
            writes.append((destination, payload))
        for relative in sorted(set(known) - set(assets)):
            destination = safe_path(root, relative)
            if destination.exists():
                if not destination.is_file() or hash_file(destination) != known[relative]:
                    _preview(result, destination, None, diff=diff)
                    result.conflicts.append(f'{destination}: obsolete file has local changes')
                else:
                    deletes.append(destination)
        record = {'schema_version': 1, 'package_version': package_version(),
                  'host': name, 'scope': scope, 'hashes': hashes}
        payload = (json.dumps(record, indent=2, sort_keys=True) + '\n').encode()
        if not manifest_path.exists() or manifest_path.read_bytes() != payload:
            writes.append((manifest_path, payload))
    for destination, payload in writes:
        _preview(result, destination, payload, diff=diff)
    for destination in deletes:
        _preview(result, destination, None, diff=diff)
    if result.conflicts or dry_run or diff:
        return result
    for destination, payload in writes:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payload)
        result.written_files.append(str(destination))
    for destination in deletes:
        destination.unlink()
        result.written_files.append(str(destination))
    return result


def uninstall_skill(repo_root: Path, *, host: str = 'all', scope: str = 'user',
                    dry_run: bool = False, diff: bool = False) -> SyncResult:
    """Remove only files whose checksums match the ownership manifest; keep everything else."""
    result = SyncResult()
    deletes: list[Path] = []
    roots: list[Path] = []
    candidates = list(skill_destinations(repo_root, host=host, scope=scope).values())
    legacy = legacy_codex_destination(host=host, scope=scope)
    if legacy is not None:
        candidates.append(legacy)
    for root in candidates:
        manifest_path = safe_path(root, SKILL_MANIFEST)
        manifest = _load_manifest(manifest_path)
        if manifest is None:
            if root.exists():
                result.conflicts.append(f'{root}: not managed by Quill; remove it manually')
            continue
        for relative, digest in sorted(manifest['hashes'].items()):
            destination = safe_path(root, relative)
            if not destination.exists():
                continue
            if not destination.is_file() or hash_file(destination) != digest:
                result.conflicts.append(f'{destination}: locally modified')
            else:
                deletes.append(destination)
        deletes.append(manifest_path)
        roots.append(root)
    for destination in deletes:
        _preview(result, destination, None, diff=diff)
    if result.conflicts or dry_run or diff:
        return result
    for destination in deletes:
        destination.unlink()
        result.written_files.append(str(destination))
    for root in roots:
        directories = sorted((p for p in root.rglob('*') if p.is_dir() and not p.is_symlink()),
                             key=lambda p: len(p.parts), reverse=True)
        for directory in (*directories, root):
            if not any(directory.iterdir()):
                directory.rmdir()
    return result
