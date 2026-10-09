from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from quill import skills

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def homes(tmp_path, monkeypatch):
    home = tmp_path / 'home'
    home.mkdir()
    monkeypatch.setattr(Path, 'home', classmethod(lambda cls: home))
    monkeypatch.delenv('CODEX_HOME', raising=False)
    return home


def test_repository_validator_passes():
    spec = importlib.util.spec_from_file_location('validate', ROOT / 'scripts/validate.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.validate() == []


def test_uninstall_removes_owned_files_and_keeps_personal_ones(tmp_path, homes):
    skills.install_skill(tmp_path)
    targets = skills.skill_destinations(tmp_path, host='all', scope='user')
    (targets['claude'] / 'personal.md').write_text('keep')
    result = skills.uninstall_skill(tmp_path)
    assert not result.conflicts
    assert not targets['codex'].exists()
    assert sorted(p.name for p in targets['claude'].rglob('*')) == ['personal.md']


def test_uninstall_refuses_modified_files_on_every_host(tmp_path, homes):
    skills.install_skill(tmp_path)
    targets = skills.skill_destinations(tmp_path, host='all', scope='user')
    (targets['claude'] / 'references/editing.md').write_text('my edits')
    result = skills.uninstall_skill(tmp_path)
    assert result.conflicts and not result.written_files
    assert (targets['codex'] / 'SKILL.md').is_file()
    assert (targets['claude'] / skills.SKILL_MANIFEST).is_file()


def test_uninstall_leaves_unmanaged_copies_alone(tmp_path, homes):
    target = homes / '.claude/skills/quill'
    target.mkdir(parents=True)
    (target / 'SKILL.md').write_text('hand-installed')
    assert skills.uninstall_skill(tmp_path, host='claude').conflicts
    assert (target / 'SKILL.md').read_text() == 'hand-installed'


def test_copy_install_defers_to_installer_symlink(tmp_path, homes):
    clone = tmp_path / 'clone/skills/quill'
    clone.mkdir(parents=True)
    link = homes / '.claude/skills/quill'
    link.parent.mkdir(parents=True)
    link.symlink_to(clone, target_is_directory=True)
    with pytest.raises(ValueError, match='install.sh'):
        skills.install_skill(tmp_path, host='claude')
    assert list(clone.iterdir()) == []


@pytest.mark.skipif(shutil.which('git') is None or not (ROOT / '.git').exists(), reason='needs a git checkout')
def test_installer_links_detected_agents(tmp_path):
    """Install from this checkout into a fake HOME; never schedules real jobs."""
    home = tmp_path / 'home'
    for agent in ('.claude', '.codex'):
        (home / agent).mkdir(parents=True)
    branch = subprocess.run(['git', '-C', ROOT, 'branch', '--show-current'],
                            capture_output=True, text=True, check=True).stdout.strip()
    if not branch:
        pytest.skip('detached HEAD')
    env = {'PATH': os.environ['PATH'], 'HOME': str(home), 'XDG_STATE_HOME': str(tmp_path / 'state'),
           'QUILL_HOME': str(tmp_path / 'clone'), 'QUILL_REPO': str(ROOT), 'QUILL_REF': branch}
    run = lambda *args: subprocess.run(['bash', ROOT / 'install.sh', *args], env=env,
                                       capture_output=True, text=True, check=True).stdout
    run('install', '--no-auto-update')
    for skills_dir in ('.claude/skills', '.agents/skills'):
        link = home / skills_dir / 'quill'
        assert link.is_symlink() and (link / 'SKILL.md').is_file()
    status = run('status')
    assert 'version:' in status and 'auto-update: off' in status
    assert 'up to date' in run('update')
