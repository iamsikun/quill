"""Exercise installer lifecycle with local Git fixtures and a fake uv executable."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DEFINITIONS = (ROOT / 'install.sh').read_text().rsplit('\nmain "$@"', 1)[0]


def git(*args):
    return subprocess.run(['git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                           *map(str, args)], check=True, capture_output=True, text=True).stdout


@pytest.fixture
def installer(tmp_path):
    origin = tmp_path / 'origin'
    git('init', '-b', 'stable', origin)
    (origin / 'skills/quill').mkdir(parents=True)
    (origin / 'skills/quill/SKILL.md').write_text('  version: "0.3.0"\n')
    (origin / 'pyproject.toml').write_text('version = "0.3.0"\n')
    git('-C', origin, 'add', '.')
    git('-C', origin, 'commit', '-m', 'fixture')
    fake_uv = tmp_path / 'uv'
    fake_uv.write_text('''#!/bin/bash
set -eu
case "$1 $2" in
  'tool dir') printf '%s\\n' "$QUILL_TEST_ROOT/tools" ;;
  'tool install')
    printf 'attempt\\n' >> "$QUILL_TEST_ROOT/attempts"
    [ ! -f "$QUILL_TEST_ROOT/fail" ] || exit 1
    mkdir -p "$QUILL_TEST_ROOT/tools/quill"
    printf 'editable = "%s"\\n' "$QUILL_HOME" > "$QUILL_TEST_ROOT/tools/quill/uv-receipt.toml"
    ;;
  'tool uninstall')
    printf 'uninstall\\n' >> "$QUILL_TEST_ROOT/uninstalls"
    rm -f "$QUILL_TEST_ROOT/tools/quill/uv-receipt.toml"
    ;;
  *) exit 2 ;;
esac
''')
    fake_uv.chmod(0o755)
    env = {**os.environ, 'QUILL_HOME': str(tmp_path / 'clone'), 'QUILL_REPO': str(origin),
           'QUILL_REF': 'stable', 'XDG_STATE_HOME': str(tmp_path / 'state'), 'QUILL_TEST_ROOT': str(tmp_path)}
    # All host mutations are redirected to fixtures; the real HOME is never used.
    overrides = '''
agent_skill_dirs() { printf '%s\\n' "$QUILL_TEST_ROOT/agent"; }
unschedule_updates() { printf 'off\\n' > "$QUILL_TEST_ROOT/scheduler"; }
schedule_updates() { printf 'on\\n' > "$QUILL_TEST_ROOT/scheduler"; }
unlink_skill() { :; }
find_uv() { printf '%s\\n' "$QUILL_TEST_ROOT/uv"; }
'''

    def run(command):
        return subprocess.run(['bash'], input=DEFINITIONS + overrides + '\n' + command,
                              env=env, capture_output=True, text=True)

    return tmp_path, run


def test_install_preserves_external_symlink_and_disables_existing_schedule(installer):
    root, run = installer
    custom = root / 'custom'
    custom.mkdir()
    (custom / 'SKILL.md').write_text('personal skill')
    (root / 'agent').mkdir()
    (root / 'agent/quill').symlink_to(custom)
    result = run('cmd_install --no-auto-update --no-cli')
    assert result.returncode == 0, result.stderr
    assert (root / 'agent/quill').resolve() == custom
    assert (custom / 'SKILL.md').read_text() == 'personal skill'
    assert (root / 'scheduler').read_text() == 'off\n'


def test_refresh_retries_after_git_has_already_advanced(installer):
    root, run = installer
    assert run('cmd_install --no-auto-update').returncode == 0
    (root / 'origin/pyproject.toml').write_text('version = "0.4.0"\n')
    (root / 'origin/skills/quill/SKILL.md').write_text('  version: "0.4.0"\n')
    git('-C', root / 'origin', 'add', '.')
    git('-C', root / 'origin', 'commit', '-m', 'next release')
    (root / 'fail').touch()
    failed = run('cmd_update')
    assert failed.returncode != 0
    assert 'next update will retry' in failed.stdout
    assert '0.4.0' in (root / 'clone/pyproject.toml').read_text()
    assert (root / 'state/quill/last-error').exists()
    (root / 'fail').unlink()
    completed = run('cmd_update')
    assert completed.returncode == 0, completed.stderr
    assert 'refreshed' in completed.stdout
    assert (root / 'attempts').read_text().count('attempt') == 3
    assert not (root / 'state/quill/last-error').exists()
    assert run('cmd_update').returncode == 0
    assert (root / 'attempts').read_text().count('attempt') == 3


def test_refresh_recovers_missing_receipt_but_preserves_external_install(installer):
    root, run = installer
    assert run('cmd_install --no-auto-update').returncode == 0
    receipt = root / 'tools/quill/uv-receipt.toml'
    receipt.unlink()
    assert run('cmd_update').returncode == 0
    assert receipt.exists()
    receipt.write_text('editable = "/some/other/quill"\n')
    before = (root / 'attempts').read_text()
    assert run('cmd_update').returncode != 0
    assert (root / 'attempts').read_text() == before
    assert run('cmd_uninstall').returncode == 0
    assert receipt.read_text() == 'editable = "/some/other/quill"\n'
    assert not (root / 'uninstalls').exists()


@pytest.mark.parametrize('change', ['commit', 'branch', 'dirty', 'ignored', 'unowned'])
def test_uninstall_preserves_personal_work_and_unowned_clones(installer, change):
    root, run = installer
    assert run('cmd_install --no-auto-update --no-cli').returncode == 0
    clone = root / 'clone'
    if change in {'commit', 'branch', 'dirty'}:
        (clone / 'personal.txt').write_text('Do not lose this work')
        if change != 'dirty':
            git('-C', clone, 'add', '.')
            git('-C', clone, 'commit', '-m', 'unpublished work')
            if change == 'branch':
                git('-C', clone, 'branch', 'personal')
                git('-C', clone, 'checkout', 'origin/stable')
    elif change == 'ignored':
        (clone / '.git/info/exclude').write_text('personal.txt\n')
        (clone / 'personal.txt').write_text('ignored personal file')
    else:
        (root / 'state/quill/clone').unlink()
    result = run('cmd_uninstall')
    assert result.returncode == 0, result.stderr
    assert clone.is_dir()
    assert 'kept' in result.stdout


def test_uninstall_removes_clean_owned_published_clone(installer):
    root, run = installer
    assert run('cmd_install --no-auto-update --no-cli').returncode == 0
    assert run('cmd_uninstall').returncode == 0
    assert not (root / 'clone').exists()


def test_update_preserves_dirty_clone_even_when_changes_do_not_overlap(installer):
    root, run = installer
    assert run('cmd_install --no-auto-update --no-cli').returncode == 0
    (root / 'clone/personal.txt').write_text('work')
    result = run('cmd_update')
    assert result.returncode != 0
    assert (root / 'clone/personal.txt').read_text() == 'work'
