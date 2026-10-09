from __future__ import annotations

import json
from pathlib import Path

import pytest

from quill import skills
from quill.cli import main
from quill.doctor import diagnose


def snapshot(root):
    return {str(path.relative_to(root)): path.read_bytes() for path in root.rglob('*') if path.is_file()}


def test_sync_preview_shows_diff_and_obsolete_files_without_mutating(tmp_path, monkeypatch):
    payload = dict(skills.skill_bytes(), **{'obsolete.md': b'Old instructions\n'})
    monkeypatch.setattr(skills, 'skill_bytes', lambda: payload)
    skills.install_skill(tmp_path, scope='project')
    payload = {name: data for name, data in payload.items() if name != 'obsolete.md'}
    payload['references/editing.md'] += b'\nA fixture change.\n'
    before = snapshot(tmp_path)
    result = skills.install_skill(tmp_path, scope='project', sync=True, diff=True)
    assert not result.conflicts and not result.written_files
    assert any('delete:' in change and 'obsolete.md' in change for change in result.planned_changes)
    assert '+A fixture change.' in ''.join(result.diffs)
    assert snapshot(tmp_path) == before
    applied = skills.install_skill(tmp_path, scope='project', sync=True)
    assert applied.written_files
    assert not (tmp_path / '.agents/skills/quill/obsolete.md').exists()


def test_preview_displays_conflict_and_preserves_preferences(tmp_path):
    skills.install_skill(tmp_path, scope='project')
    customized = tmp_path / '.agents/skills/quill/references/editing.md'
    customized.write_text('My customized copy\n')
    preference = tmp_path / '.quill/preferences.md'
    preference.parent.mkdir()
    preference.write_text('Personal preferences outside the skill.\n')
    before = snapshot(tmp_path)
    result = skills.install_skill(tmp_path, scope='project', sync=True, diff=True)
    assert result.conflicts
    assert '-My customized copy' in ''.join(result.diffs)
    assert snapshot(tmp_path) == before


def test_cli_install_preview_does_not_create_directories(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as stopped:
        main(['skill', 'install', '--scope', 'project', '--dry-run'])
    assert stopped.value.code == 0
    assert 'would create:' in capsys.readouterr().out
    assert not list(tmp_path.iterdir())


def test_uninstall_preview_is_read_only(tmp_path):
    skills.install_skill(tmp_path, scope='project')
    before = snapshot(tmp_path)
    result = skills.uninstall_skill(tmp_path, scope='project', diff=True)
    assert result.planned_changes and not result.written_files
    assert snapshot(tmp_path) == before


def test_doctor_reports_versions_paths_conflicts_and_update_failure(tmp_path, monkeypatch):
    home, project = tmp_path / 'home', tmp_path / 'project'
    home.mkdir()
    project.mkdir()
    monkeypatch.setattr(Path, 'home', classmethod(lambda cls: home))
    monkeypatch.delenv('CODEX_HOME', raising=False)
    monkeypatch.setenv('XDG_STATE_HOME', str(tmp_path / 'state'))
    monkeypatch.setenv('QUILL_HOME', str(tmp_path / 'missing-clone'))
    skills.install_skill(project, host='codex', scope='user')
    skills.install_skill(project, host='codex', scope='project')
    (home / '.agents/skills/quill/references/editing.md').write_text('customized')
    state = tmp_path / 'state/quill'
    state.mkdir(parents=True)
    (state / 'last-error').write_text('refresh failed; next update will retry')
    before = snapshot(tmp_path)
    report = diagnose(project)
    assert report['package_version'] and report['skill_version']
    assert len(report['installations']) == 2
    assert all(item['resolved_path'] for item in report['installations'])
    assert any('multiple Quill installations' in issue for issue in report['issues'])
    assert any('managed files changed' in issue for issue in report['issues'])
    assert any('refresh failed' in issue for issue in report['issues'])
    assert 'pdflatex' in report['dependencies'] and report['cli_install']['method']
    assert snapshot(tmp_path) == before


def test_doctor_json_and_broken_symlink_are_actionable(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(Path, 'home', classmethod(lambda cls: tmp_path))
    monkeypatch.delenv('CODEX_HOME', raising=False)
    monkeypatch.setenv('XDG_STATE_HOME', str(tmp_path / 'state'))
    monkeypatch.setenv('QUILL_HOME', str(tmp_path / 'clone'))
    project = tmp_path / 'project'
    project.mkdir()
    monkeypatch.chdir(project)
    link = tmp_path / '.agents/skills/quill'
    link.parent.mkdir(parents=True)
    link.symlink_to(tmp_path / 'absent')
    with pytest.raises(SystemExit) as stopped:
        main(['doctor', '--json'])
    assert stopped.value.code == 1
    report = json.loads(capsys.readouterr().out)
    assert report['installations'][0]['method'] == 'symlink'
    assert report['installations'][0]['error']
