from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest
import yaml

from quill import skills
from quill.cli import REMOVED_COMMANDS, main
from quill.sync import hash_bytes, resource_bytes, safe_path

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def homes(tmp_path, monkeypatch):
    home = tmp_path / 'home'
    home.mkdir()
    monkeypatch.setattr(Path, 'home', classmethod(lambda cls: home))
    monkeypatch.delenv('CODEX_HOME', raising=False)
    return home


def test_skill_metadata_references_and_canonical_payload():
    source = ROOT / 'skills/quill'
    payloads = skills.skill_bytes()
    assert payloads == resource_bytes(source)
    manifest = payloads['SKILL.md'].decode()
    header = yaml.safe_load(manifest.split('---', 2)[1])
    assert header['name'] == 'quill'
    assert header['description']
    for relative, payload in payloads.items():
        if relative.endswith('.md'):
            for link in re.findall(r'\]\(([^)]+)\)', payload.decode()):
                if '://' not in link:
                    assert (source / relative).parent.joinpath(link).is_file(), (relative, link)
    ui = yaml.safe_load(payloads['agents/openai.yaml'])
    assert ui['policy']['allow_implicit_invocation'] is True


@pytest.mark.parametrize('scope', ['user', 'project'])
@pytest.mark.parametrize('host', ['codex', 'claude', 'all'])
def test_install_and_sync_across_hosts(tmp_path, homes, scope, host):
    repo = tmp_path / 'project'
    repo.mkdir()
    result = skills.install_skill(repo, host=host, scope=scope)
    assert not result.conflicts
    expected_hosts = skills.HOSTS if host == 'all' else (host,)
    for name in expected_hosts:
        base = homes if scope == 'user' else repo
        directory = '.codex' if name == 'codex' and scope == 'user' else '.agents' if name == 'codex' else '.claude'
        target = base / directory / 'skills/quill'
        for relative, payload in skills.skill_bytes().items():
            assert (target / relative).read_bytes() == payload
        assert json.loads((target / skills.SKILL_MANIFEST).read_text())['host'] == name
    assert not skills.install_skill(repo, host=host, scope=scope).written_files
    assert not skills.install_skill(repo, host=host, scope=scope, sync=True).written_files
    assert not (repo / 'paper').exists()
    assert not (repo / '.quill').exists()


def test_configured_codex_home(tmp_path, homes, monkeypatch):
    configured = tmp_path / 'custom-codex'
    monkeypatch.setenv('CODEX_HOME', str(configured))
    skills.install_skill(tmp_path, host='codex')
    assert (configured / 'skills/quill/SKILL.md').is_file()
    assert not (homes / '.codex').exists()


def test_update_preserves_unknown_files_and_prunes_owned_obsolete(tmp_path, homes, monkeypatch):
    original = skills.skill_bytes()
    monkeypatch.setattr(skills, 'skill_bytes', lambda: {**original, 'obsolete.md': b'old'})
    skills.install_skill(tmp_path, host='codex')
    target = homes / '.codex/skills/quill'
    (target / 'personal.md').write_text('keep')
    changed = {**original, 'references/editing.md': b'Updated editing guidance.'}
    monkeypatch.setattr(skills, 'skill_bytes', lambda: changed)
    result = skills.install_skill(tmp_path, host='codex', sync=True)
    assert not result.conflicts
    assert (target / 'references/editing.md').read_bytes() == changed['references/editing.md']
    assert (target / 'personal.md').read_text() == 'keep'
    assert not (target / 'obsolete.md').exists()


def test_conflict_preflights_both_hosts(tmp_path, homes, monkeypatch):
    skills.install_skill(tmp_path)
    targets = skills.skill_destinations(tmp_path, host='all', scope='user')
    (targets['claude'] / 'references/editing.md').write_text('my edits')
    original = skills.skill_bytes()
    monkeypatch.setattr(skills, 'skill_bytes', lambda: {**original, 'references/editing.md': b'new release'})
    result = skills.install_skill(tmp_path, sync=True)
    assert result.conflicts and not result.written_files
    assert (targets['codex'] / 'references/editing.md').read_bytes() == original['references/editing.md']
    assert (targets['claude'] / 'references/editing.md').read_text() == 'my edits'


def test_obsolete_modified_file_blocks_update(tmp_path, homes, monkeypatch):
    original = skills.skill_bytes()
    monkeypatch.setattr(skills, 'skill_bytes', lambda: {**original, 'old.md': b'old'})
    skills.install_skill(tmp_path, host='codex')
    target = homes / '.codex/skills/quill'
    (target / 'old.md').write_text('local edits')
    monkeypatch.setattr(skills, 'skill_bytes', lambda: original)
    assert skills.install_skill(tmp_path, host='codex', sync=True).conflicts
    assert (target / 'old.md').read_text() == 'local edits'


def test_sync_requires_ownership_and_install_protects_existing(tmp_path, homes):
    assert skills.install_skill(tmp_path, host='codex', sync=True).conflicts
    target = homes / '.codex/skills/quill'
    target.mkdir(parents=True)
    (target / 'SKILL.md').write_text('existing skill')
    assert skills.install_skill(tmp_path, host='codex').conflicts
    assert not (target / skills.SKILL_MANIFEST).exists()


@pytest.mark.parametrize('relative', ['../outside', '/outside', 'a/../../outside', 'a\\outside', './x', '.'])
def test_reject_unsafe_manifest_paths(tmp_path, relative):
    with pytest.raises(ValueError):
        safe_path(tmp_path, relative)


def test_manifest_cannot_delete_outside_skill(tmp_path, homes):
    skills.install_skill(tmp_path, host='codex')
    manifest = homes / '.codex/skills/quill' / skills.SKILL_MANIFEST
    data = json.loads(manifest.read_text())
    outside = homes / '.codex/skills/outside'
    outside.write_text('private data')
    data['hashes']['../outside'] = hash_bytes(outside.read_bytes())
    manifest.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        skills.install_skill(tmp_path, host='codex', sync=True)
    assert outside.read_text() == 'private data'


@pytest.mark.parametrize('location', ['.agents', '.agents/skills/quill', '.agents/skills/quill/references'])
def test_refuse_symlinked_project_destinations(tmp_path, location):
    outside = tmp_path / 'outside'
    outside.mkdir()
    repo = tmp_path / 'repo'
    repo.mkdir()
    link = repo / location
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError):
        skills.install_skill(repo, host='codex', scope='project')
    assert list(outside.iterdir()) == []


@pytest.mark.parametrize('command', list(REMOVED_COMMANDS))
def test_removed_commands_fail_with_guidance(command, capsys):
    with pytest.raises(SystemExit) as exc:
        main([command])
    assert exc.value.code == 2
    assert 'removed in Quill 0.2' in capsys.readouterr().err


def test_installed_references_are_independent_of_cwd(tmp_path, homes, monkeypatch):
    skills.install_skill(tmp_path, host='codex')
    target = homes / '.codex/skills/quill'
    other = tmp_path / 'another-project'
    other.mkdir()
    monkeypatch.chdir(other)
    for link in re.findall(r'\]\((references/[^)]+)\)', (target / 'SKILL.md').read_text()):
        assert (target / link).read_text()
    assert list(other.iterdir()) == []


def test_built_wheel_contains_identical_skill(tmp_path):
    wheel = os.environ.get('QUILL_WHEEL')
    if not wheel:
        pytest.skip('set QUILL_WHEEL after uv build to test the built distribution')
    with zipfile.ZipFile(wheel) as archive:
        actual = {name.removeprefix('quill/skill/'): archive.read(name)
                  for name in archive.namelist() if name.startswith('quill/skill/')}
    assert actual == resource_bytes(ROOT / 'skills/quill')
    result = subprocess.run([sys.executable, '-c',
        'import sys; from pathlib import Path; sys.path.insert(0, sys.argv[1]); '
        'import quill; assert sys.argv[1] in quill.__file__; '
        'from quill.skills import install_skill; from quill.sync import init_project; '
        'from quill.validate import validate_repo; root = Path.cwd(); '
        'assert not install_skill(root, host="all", scope="project").conflicts; '
        'assert (root / ".agents/skills/quill/references/editing.md").is_file(); '
        'assert (root / ".claude/skills/quill/SKILL.md").is_file(); '
        'assert not init_project(root).conflicts; assert validate_repo(root).ok',
        str(Path(wheel).resolve())], cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
