"""Read-only diagnostics for the CLI, skill installations, and update state."""
from __future__ import annotations

import json
import os
import plistlib
import shutil
import subprocess
import sys
from importlib import metadata
from pathlib import Path

import yaml

from . import __version__
from .skills import SKILL_MANIFEST, _load_manifest, skill_bytes
from .sync import hash_file, package_version, project_assets_dir


def _version(text: str) -> str | None:
    if not text.startswith('---\n'):
        return None
    data = yaml.safe_load(text.split('---', 2)[1]) or {}
    return str(data.get('metadata', {}).get('version', 'unknown'))


def diagnose(repo_root: Path) -> dict:
    issues: list[str] = []
    installations: list[dict] = []
    candidates = []
    for scope, root in (('user', Path.home()), ('project', repo_root)):
        for host, directory in (('codex', '.agents'), ('claude', '.claude')):
            candidates.append((host, scope, root / directory / 'skills/quill', None))
    legacy = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))) / 'skills/quill'
    candidates.append(('codex', 'legacy', legacy, None))
    plugins = Path.home() / '.claude/plugins/installed_plugins.json'
    if plugins.is_file():
        try:
            for name, entries in json.loads(plugins.read_text()).get('plugins', {}).items():
                if name.split('@')[0] != 'quill':
                    continue
                for entry in entries:
                    if entry.get('scope') == 'project' and Path(entry.get('projectPath', '')) != repo_root:
                        continue
                    if entry.get('installPath'):
                        candidates.append(('claude', entry.get('scope', 'plugin'),
                                           Path(entry['installPath']) / 'skills/quill', 'plugin'))
        except (OSError, ValueError, TypeError, AttributeError) as exc:
            issues.append(f'cannot inspect Claude plugin registry: {exc}')
    for host, scope, path, method in candidates:
        if not path.exists() and not path.is_symlink():
            continue
        item = dict(host=host, scope=scope, path=str(path), resolved_path=str(path.resolve()),
                    method=method or ('symlink' if path.is_symlink() else 'unmanaged copy'))
        try:
            item['version'] = _version((path / 'SKILL.md').read_text())
            manifest = _load_manifest(path / SKILL_MANIFEST)
            if manifest:
                item['method'] = 'managed copy'
                changed = [name for name, digest in manifest['hashes'].items()
                           if not (path / name).is_file() or hash_file(path / name) != digest]
                item['modified_files'] = changed
                if changed:
                    issues.append(f'{path}: {len(changed)} managed files changed or missing; preview skill sync --diff')
            if scope == 'legacy':
                issues.append(f'{path}: legacy installation; review before removing')
        except (OSError, ValueError, TypeError, AttributeError, yaml.YAMLError) as exc:
            item['error'] = str(exc)
            issues.append(f'{path}: {exc}')
        installations.append(item)
    for host in ('codex', 'claude'):
        selected = [item for item in installations if item['host'] == host]
        if len(selected) > 1:
            issues.append(f'{host}: multiple Quill installations found; retain one installation scope/method')
    tools = {name: shutil.which(name) for name in ('quill', 'uv', 'git', 'latexmk', 'pdflatex', 'bibtex', 'biber')}
    try:
        direct = json.loads(metadata.distribution('quill').read_text('direct_url.json') or '{}')
    except (metadata.PackageNotFoundError, ValueError):
        direct = {}
    cli_install = {'method': 'editable' if direct.get('dir_info', {}).get('editable') else 'package',
                   'source': direct.get('url'), 'module': str(Path(__file__).parent)}
    state = Path(os.environ.get('XDG_STATE_HOME', str(Path.home() / '.local/state'))) / 'quill'
    clone = Path(os.environ.get('QUILL_HOME', str(Path.home() / '.local/share/quill')))
    update = {'clone': str(clone), 'state_directory': str(state)}
    for name in ('last-update', 'last-error', 'cli', 'cli-metadata'):
        path = state / name
        update[name] = path.read_text().strip() if path.is_file() else None
    plist = Path.home() / 'Library/LaunchAgents/io.github.iamsikun.quill.update.plist'
    update['launchd_job_file'] = str(plist) if plist.is_file() else None
    update['scheduler'] = 'not configured'
    if plist.is_file():
        try:
            job = plistlib.loads(plist.read_bytes())
            update['scheduler'] = 'launchd job configured (runtime load state not checked)'
            update['scheduled_command'] = job.get('ProgramArguments')
        except (ValueError, OSError, plistlib.InvalidFileException) as exc:
            issues.append(f'cannot read update job: {exc}')
    elif shutil.which('crontab'):
        try:
            cron = subprocess.run(['crontab', '-l'], capture_output=True, text=True, timeout=5)
            if '# quill-auto-update' in cron.stdout:
                update['scheduler'] = 'cron job configured'
            elif cron.returncode and 'no crontab' not in cron.stderr.lower():
                update['scheduler'] = 'could not inspect crontab'
        except (OSError, subprocess.TimeoutExpired):
            update['scheduler'] = 'could not inspect crontab'
    if (clone / 'pyproject.toml').is_file() and shutil.which('git'):
        try:
            fingerprint = subprocess.run(['git', '-C', str(clone), 'hash-object', 'pyproject.toml'],
                                         capture_output=True, text=True, timeout=5)
            if fingerprint.returncode == 0:
                update['cli_refresh_pending'] = bool(update['cli'] and update['cli-metadata'] != fingerprint.stdout.strip())
                if update['cli_refresh_pending']:
                    issues.append('CLI metadata refresh pending; run install.sh update')
        except (OSError, subprocess.TimeoutExpired):
            issues.append('could not check installer metadata fingerprint')
    if update['last-error']:
        issues.append(f"installer: {update['last-error']}")
    if update['cli'] and not clone.is_dir():
        issues.append('installer CLI ownership state exists but its clone is missing')
    if package_version() != __version__:
        issues.append('CLI package metadata and runtime version differ; rerun installer update')
    try:
        bundled_version = _version(skill_bytes()['SKILL.md'].decode())
    except (OSError, ValueError, yaml.YAMLError) as exc:
        bundled_version = None
        issues.append(f'cannot read bundled skill: {exc}')
    return dict(package_version=package_version(), runtime_version=__version__, skill_version=bundled_version,
                python=sys.executable, cli_install=cli_install, project=str(repo_root), installations=installations,
                dependencies=tools, update=update,
                preferences=str(project_assets_dir(repo_root) / 'preferences.md'), issues=issues)


def format_diagnosis(report: dict) -> str:
    lines = [f"Quill CLI: {report['package_version']} (runtime {report['runtime_version']})",
             f"CLI installation: {report['cli_install']['method']} — {report['cli_install']['source'] or report['cli_install']['module']}",
             f"Bundled skill: {report['skill_version']}", f"Python: {report['python']}",
             f"Project: {report['project']}"]
    for item in report['installations']:
        lines.append(f"{item['host']} {item['scope']}: {item['method']}, version {item.get('version', 'unreadable')} — "
                     f"{item['path']} -> {item['resolved_path']}")
    if not report['installations']:
        lines.append('No skill installation found at the inspected locations.')
    for name, path in report['dependencies'].items():
        lines.append(f"{name}: {path or 'not found'}")
    for name, value in report['update'].items():
        lines.append(f"update {name}: {value or 'not recorded'}")
    lines.append(f"Optional project preferences: {report['preferences']} (attach explicitly when writing)")
    lines.extend(f"WARN: {message}" for message in report['issues'])
    lines.append('Static diagnostics only; missing LaTeX tools do not prevent ordinary writing.')
    return '\n'.join(lines)
