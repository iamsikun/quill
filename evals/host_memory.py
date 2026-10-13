"""Smoke-test real profile tools and the changes/baseline loop in authenticated CLIs.

Uses synthetic files, an isolated XDG_CONFIG_HOME outside the project, and a
project copy of the current skill. Does not alter the user's installed Quill.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

from personalization import final_text

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills/quill'
SEED = ('---\nmode: learn\n---\n# Writing profile\n\n'
        '<!-- fixture-owned: keep-this-note -->\n\n## General\n'
        '- Write "percentage points" in full, never abbreviate it. (stated)\n')
MANUSCRIPT = (
    '# Methods\n\n'
    'We utilize an instrumental-variables estimator. Shipping costs shift prices '
    'without directly affecting the outcome.\n\n'
    'We conduct a matched comparison. District pairs have the same pre-policy outcome trend.\n\n'
    'We apply a difference-in-differences estimator. Treated and comparison districts '
    'have parallel pre-policy trends.\n\n'
    '# Results\n\n'
    'The effect was 5 percentage points. The 95 percent interval was [2, 8]. '
    '\\cite{demo2024}\n')
AUTHOR_EDITS = {
    'We conduct a matched comparison. District pairs have the same pre-policy outcome trend.':
        'District pairs have the same pre-policy outcome trend, so we conduct a matched comparison.',
    'We apply a difference-in-differences estimator. Treated and comparison districts '
    'have parallel pre-policy trends.':
        'Treated and comparison districts have parallel pre-policy trends, so we apply '
        'a difference-in-differences estimator.',
    'The effect was 5 percentage points.': 'The effect was 6 percentage points.',
}
TRANSFER = ('# Methods\n\nWe quantify the effect with an instrumental-variables estimator. '
            'Route distance shifts shipping costs without directly affecting queue time.\n')


def host_command(host: str, config: Path) -> list[str]:
    if host == 'codex':
        return ['codex', 'exec', '--ephemeral', '--ignore-user-config', '--skip-git-repo-check',
                '--sandbox', 'workspace-write', '--add-dir', str(config), '--json', '-']
    return ['claude', '-p', '--no-session-persistence', '--output-format', 'stream-json',
            '--verbose', '--restricted', '--setting-sources', 'project', '--strict-mcp-config',
            '--mcp-config', '{"mcpServers":{}}', '--settings', '{"disableAllHooks":true}',
            '--permission-mode', 'dontAsk', '--add-dir', str(config),
            '--tools', 'Read,Edit,Write,Bash,Skill', '--allowedTools',
            'Read', 'Edit', 'Write', 'Skill', 'Bash', '--']


def prepare(root: Path, host: str) -> tuple[Path, Path, Path]:
    config, project, second = root / 'config', root / 'paper-one', root / 'paper-two'
    for directory in (project, second):
        agent = '.agents' if host == 'codex' else '.claude'
        shutil.copytree(SKILL, directory / agent / 'skills/quill')
    (config / 'quill').mkdir(parents=True)
    (config / 'quill/profile.md').write_text(SEED)
    (project / 'methods.md').write_text(MANUSCRIPT)
    (second / 'methods.md').write_text(TRANSFER)
    # The wrapper runs this checkout's CLI and records successful/failed commands,
    # including the manuscript bytes when changes/baseline is invoked.
    (config / 'bin').mkdir()
    wrapper = config / 'bin/quill'
    wrapper.write_text(f'''#!{sys.executable}
import hashlib, json, os, pathlib, subprocess, sys
env = dict(os.environ, PYTHONPATH={str(ROOT / 'src')!r})
file = pathlib.Path('methods.md')
digest = hashlib.sha256(file.read_bytes()).hexdigest() if file.is_file() else None
run = subprocess.run([{sys.executable!r}, '-m', 'quill', *sys.argv[1:]],
                     capture_output=True, text=True, env=env)
with open({str(config / 'cli-events.jsonl')!r}, 'a') as stream:
    stream.write(json.dumps(dict(stage=os.environ.get('QUILL_EVAL_STAGE'), args=sys.argv[1:],
        cwd=str(pathlib.Path.cwd()), manuscript_sha256=digest, exit_code=run.returncode,
        stdout=run.stdout, stderr=run.stderr)) + '\\n')
sys.stdout.write(run.stdout)
sys.stderr.write(run.stderr)
sys.exit(run.returncode)
''')
    wrapper.chmod(0o755)
    return config, project, second


def prompt(host: str, stage: str, project: Path, config: Path) -> str:
    skill = project / ('.agents' if host == 'codex' else '.claude') / 'skills/quill/SKILL.md'
    tasks = {
        'learn': 'Learn my writing style: in methods sections, use "We estimate" rather than '
                 '"We quantify" when describing estimation. Line-edit only the first methods '
                 'paragraph in methods.md; leave all subsequent paragraphs exactly as they are.',
        'changes': 'I edited methods.md myself since your last version. Line-edit only the first '
                   'methods paragraph; leave all other paragraphs exactly as they are.',
        'transfer': 'Line-edit the methods paragraph in methods.md for a research audience.',
    }
    return (f'Use Quill from {skill}. {tasks[stage]}\n'
            'This is a disposable, single-author synthetic manuscript. Work in the actual files '
            'using the skill workflow, then give a brief summary. The quill CLI on PATH belongs '
            f'to the tested checkout. XDG_CONFIG_HOME is {config}. A shared profile already '
            f'exists at {config / "quill/profile.md"}; read it from disk before editing. '
            'Do not access any other personal memory. Only the current project '
            'and this isolated config folder may be changed. Do not use connected services, '
            'delegate, or change settings or installed tools.')


def tool_trace(stdout: str) -> list[dict]:
    """Keep tool evidence without unrelated account/session metadata."""
    trace, calls = [], {}
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        item = event.get('item', {})
        if event.get('type') in ('error', 'turn.failed'):
            trace.append({k: v for k, v in event.items() if k != 'id'})
        if event.get('type') == 'item.completed' and item.get('type') in (
                'command_execution', 'file_change', 'mcp_tool_call'):
            trace.append({k: v for k, v in item.items() if k != 'id'})
        if event.get('type') in ('assistant', 'user'):
            content = event.get('message', {}).get('content', [])
            if isinstance(content, list):
                for part in content:
                    if part.get('type') == 'tool_use':
                        calls[part['id']] = {'tool_name': part['name'], 'tool_input': part['input']}
                    if part.get('type') in ('tool_use', 'tool_result'):
                        entry = {k: v for k, v in part.items() if k not in ('id', 'tool_use_id')}
                        if part.get('type') == 'tool_result':
                            entry.update(calls.get(part.get('tool_use_id'), {}))
                        trace.append(entry)
    return trace


def snapshot(project: Path, config: Path) -> dict:
    paths = {'manuscript': project / 'methods.md', 'baseline': project / '.quill/style/baselines/methods.md',
             'profile': config / 'quill/profile.md', 'examples': config / 'quill/examples.md'}
    return {name: path.read_text() if path.is_file() else None for name, path in paths.items()}


def run_case(host: str, timeout: int) -> dict:
    record = {'host': host, 'host_version': subprocess.run([host, '--version'], capture_output=True,
              text=True, timeout=15).stdout.strip(), 'stages': [],
              'skill_hashes': {p.relative_to(SKILL).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in sorted(SKILL.rglob('*')) if p.is_file()},
              'limitations': 'Explicit skill path; isolated permitted storage; one sample per stage. '
                             'Not an implicit-discovery, denied-permission, or writing-quality benchmark.'}
    with tempfile.TemporaryDirectory(prefix='quill-host-memory-') as tmp:
        root = Path(tmp).resolve()
        config, project, second = prepare(root, host)
        env = dict(os.environ, XDG_CONFIG_HOME=str(config),
                   PATH=str(config / 'bin') + os.pathsep + os.environ['PATH'])
        for stage in ('learn', 'changes', 'transfer'):
            if stage == 'changes':
                text = (project / 'methods.md').read_text()
                for before, after in AUTHOR_EDITS.items():
                    if text.count(before) != 1:
                        record['error'] = 'First stage changed a protected author-edit fixture'
                        return record
                    text = text.replace(before, after)
                (project / 'methods.md').write_text(text)
            current = second if stage == 'transfer' else project
            stage_env = dict(env, QUILL_EVAL_STAGE=stage)
            item = {'stage': stage, 'before': snapshot(current, config),
                    'prompt': prompt(host, stage, current, config), 'command': host_command(host, config)}
            start = time.monotonic()
            try:
                done = subprocess.run(item['command'], input=item['prompt'], cwd=current,
                                      env=stage_env, capture_output=True, text=True, timeout=timeout)
                item.update(exit_code=done.returncode, response=final_text(done.stdout),
                            tool_trace=tool_trace(done.stdout), stderr=done.stderr)
            except subprocess.TimeoutExpired as exc:
                stdout = exc.stdout.decode(errors='replace') if isinstance(exc.stdout, bytes) else exc.stdout or ''
                item.update(error='host timeout', tool_trace=tool_trace(stdout))
            except OSError as exc:
                item['error'] = str(exc)
            item['elapsed_seconds'] = round(time.monotonic() - start, 2)
            item['after'] = snapshot(current, config)
            log = config / 'cli-events.jsonl'
            item['cli_events'] = [json.loads(line) for line in log.read_text().splitlines()
                                  if json.loads(line)['stage'] == stage] if log.exists() else []
            item['checks'] = checks(item)
            record['stages'].append(item)
            print(f'{host} {stage}: {item["checks"]}', flush=True)
            if item.get('error') or item.get('exit_code') != 0:
                record['error'] = f'{stage}: host failed'
                break
        # Replace machine-specific paths in saved prompts and tool evidence.
        encoded = json.dumps(record).replace(str(root), '<fixture>').replace(str(ROOT), '<checkout>')
        return json.loads(encoded.replace(str(Path.home()), '<home>'))


def checks(stage: dict) -> dict[str, bool]:
    before, after, events = stage['before'], stage['after'], stage['cli_events']
    changed = [e for e in events if e['args'][:2] == ['style', 'changes'] and e['exit_code'] == 0]
    saved = [e for e in events if e['args'][:2] == ['style', 'baseline'] and e['exit_code'] == 0]
    digest = hashlib.sha256(before['manuscript'].encode()).hexdigest()
    result = {
        'profile_marker_preserved': '<!-- fixture-owned: keep-this-note -->' in (after['profile'] or ''),
        'profile_read_from_disk': profile_read(stage.get('tool_trace', [])),
        'changes_before_edit': any(e['manuscript_sha256'] == digest for e in changed),
        'baseline_matches_final_file': after['baseline'] == after['manuscript'] and bool(saved),
        'examples_written': bool(after['examples']),
    }
    if stage['stage'] == 'learn':
        result['profile_updated'] = before['profile'] != after['profile']
    if stage['stage'] == 'changes':
        result['profile_updated_after_author_edits'] = before['profile'] != after['profile']
        result['number_change_flagged'] = any('changed number' in e['stdout'] for e in changed)
        result['protected_paragraphs_preserved'] = (
            before['manuscript'].split('\n\n', 2)[2] == after['manuscript'].split('\n\n', 2)[2])
    if stage['stage'] == 'transfer':
        text = after['manuscript'].lower()
        result['stated_preference_applied'] = bool(re.search(r'\bestimate[sd]?\b', text)) and not re.search(r'\bquantif\w*', text)
        result['profile_unchanged_without_new_feedback'] = before['profile'] == after['profile']
    return result


def profile_read(trace: list[dict]) -> bool:
    for event in trace:
        # A command may read the file internally to preserve author-owned text
        # rather than printing its entire contents into the tool output.
        if event.get('type') == 'command_execution' and event.get('exit_code') == 0:
            command = event.get('command', '')
            if 'profile.md' in command and 'profile.read_text()' in command:
                return True
        if event.get('type') == 'tool_result' and not event.get('is_error'):
            if event.get('tool_name') == 'Read' and 'profile.md' in json.dumps(event.get('tool_input', {})):
                return True
        output = event.get('aggregated_output', event.get('content', ''))
        if 'fixture-owned: keep-this-note' in json.dumps(output):
            return True
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', choices=('codex', 'claude'), required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--timeout', type=int, default=240)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('refusing to overwrite an evaluation record')
    record = run_case(args.host, args.timeout)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as stream:
        json.dump(record, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(args.output)
    if record.get('error') or any(not all(stage['checks'].values()) for stage in record['stages']):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
