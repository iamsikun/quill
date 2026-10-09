from __future__ import annotations

from pathlib import Path

import pytest

from quill.manifest import InstallManifest
from quill.migration import migrate_project
from quill.sync import MANIFEST_PATH, hash_bytes


def _legacy(repo: Path, payloads: dict[str, bytes]) -> None:
    for relative, payload in payloads.items():
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    InstallManifest.create('0.1.0', adapters=['claude', 'codex'],
        managed_files_by_scope={'_core': list(payloads)},
        hashes={p: hash_bytes(b) for p, b in payloads.items()}).save(repo / MANIFEST_PATH)


def _snapshot(repo):
    return {p.relative_to(repo).as_posix(): p.read_bytes() for p in repo.rglob('*') if p.is_file()}


def test_migration_dry_run_apply_and_idempotence(tmp_path):
    _legacy(tmp_path, {'.claude/commands/draft-paper.md': b'old command',
                      '.pepper/writing-style.md': b'old rules',
                      '.pepper/config.yaml': b'custom config',
                      'paper/conference/sections/introduction.tex': b'manuscript'})
    agents = tmp_path / 'AGENTS.md'
    agents.write_bytes(b'User rules\r\n<!-- pepper:start -->\r\nOld rules\r\n<!-- pepper:end -->\r\nOther rules\r\n')
    before = _snapshot(tmp_path)
    preview = migrate_project(tmp_path, dry_run=True)
    assert not preview.conflicts
    assert _snapshot(tmp_path) == before
    result = migrate_project(tmp_path)
    assert result == preview
    assert not (tmp_path / '.claude/commands/draft-paper.md').exists()
    assert agents.read_bytes() == b'User rules\r\nOther rules\r\n'
    assert (tmp_path / '.pepper/config.yaml').read_bytes() == b'custom config'
    assert (tmp_path / 'paper/conference/sections/introduction.tex').read_bytes() == b'manuscript'
    assert not migrate_project(tmp_path).updated_files
    assert not migrate_project(tmp_path).removed_files


def test_modified_owned_and_unowned_files_are_preserved(tmp_path):
    _legacy(tmp_path, {'.claude/settings.json': b'{"PAPER_SYSTEM_VERSION": "3.0"}',
                      '.claude/agents/copyeditor.md': b'old'})
    settings = tmp_path / '.claude/settings.json'
    settings.write_bytes(b'{"permissions": {"allow": ["custom"]}}')
    unowned = tmp_path / '.claude/commands/polish.md'
    unowned.parent.mkdir()
    unowned.write_text('personal command')
    unrelated = tmp_path / '.claude/agents/my-agent.md'
    unrelated.write_text('personal agent')
    result = migrate_project(tmp_path)
    assert len(result.conflicts) == 2
    assert settings.read_bytes() == b'{"permissions": {"allow": ["custom"]}}'
    assert unowned.read_text() == 'personal command'
    assert unrelated.read_text() == 'personal agent'
    assert not (tmp_path / '.claude/agents/copyeditor.md').exists()


def test_settings_deleted_only_when_manifest_owned_and_unchanged(tmp_path):
    _legacy(tmp_path, {'.claude/settings.json': b'original settings'})
    assert not migrate_project(tmp_path).conflicts
    assert not (tmp_path / '.claude/settings.json').exists()


def test_unrelated_settings_and_manuscript_do_not_trigger_migration(tmp_path):
    path = tmp_path / '.claude/settings.json'
    path.parent.mkdir()
    path.write_text('{"permissions": {}}')
    before = _snapshot(tmp_path)
    assert not migrate_project(tmp_path).conflicts
    assert _snapshot(tmp_path) == before


@pytest.mark.parametrize('text', ['<!-- pepper:start -->\nunfinished',
    '<!-- pepper:end -->\n<!-- pepper:start -->',
    '<!-- pepper:start -->\nx\n<!-- pepper:end -->\n<!-- pepper:start -->'])
def test_malformed_markers_preserved(tmp_path, text):
    path = tmp_path / 'AGENTS.md'
    path.write_text(text)
    assert migrate_project(tmp_path).conflicts
    assert path.read_text() == text


def test_manifest_cannot_remove_arbitrary_or_symlinked_files(tmp_path):
    outside = tmp_path / 'outside.md'
    outside.write_text('keep')
    repo = tmp_path / 'repo'
    repo.mkdir()
    _legacy(repo, {'my-file.md': b'keep too', '.claude/agents/copyeditor.md': b'old'})
    link = repo / '.claude/agents/copyeditor.md'
    link.unlink()
    link.symlink_to(outside)
    assert migrate_project(repo).conflicts
    assert outside.read_text() == 'keep'
    assert (repo / 'my-file.md').read_text() == 'keep too'
