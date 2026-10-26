"""Run one synthetic evaluation in a disposable host session, with no grading leakage."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills/quill'
ARMS = ('plain', 'core', 'references', 'implicit', 'explicit')


def build_prompt(case: dict, arm: str, host: str, skill: Path = SKILL) -> str:
    parts = ['Complete this synthetic writing task. Return the answer in at most 350 words. '
             'Do not write files or access external services.']
    if arm in ('plain', 'core', 'references'):
        parts.append('All permitted context is included below. Do not use tools or load additional instructions.')
    if arm in ('core', 'references'):
        parts.append(skill.joinpath('SKILL.md').read_text())
    if arm == 'references':
        # A frozen earlier version may lack a newer reference; it then gets the ones it has.
        for relative in case['references']:
            if skill.joinpath('references', relative).is_file():
                parts.append(skill.joinpath('references', relative).read_text())
    parts.append(case['prompt'])
    for relative in case.get('supplied', []):
        parts.append('Supplied by the user:\n' + (ROOT / 'evals' / relative).read_text())
    parts.append('Source material:\n' + case['source'])
    prompt = '\n\n'.join(parts)
    if arm == 'explicit':
        prompt = ('Use $quill.\n\n' if host == 'codex' else '/quill\n\n') + prompt
    return prompt


def host_command(host: str, arm: str) -> list[str]:
    if host == 'codex':
        return ['codex', 'exec', '--ephemeral', '--skip-git-repo-check',
                '--sandbox', 'read-only', '--json', '-']
    command = ['claude', '-p', '--no-session-persistence', '--output-format', 'stream-json',
               '--verbose', '--strict-mcp-config', '--mcp-config', '{"mcpServers":{}}']
    if arm in ('plain', 'core', 'references'):
        command += ['--safe-mode', '--disable-slash-commands', '--tools', '']
    else:
        command += ['--tools', 'Read,Skill', '--allowedTools', 'Read,Skill',
                    '--setting-sources', 'project', '--settings', '{"disableAllHooks":true}']
    return command


def main() -> None:
    cases = json.loads(Path(__file__).with_name('cases.json').read_text())
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', choices=('codex', 'claude'), required=True)
    parser.add_argument('--arm', choices=ARMS, required=True)
    parser.add_argument('--case', choices=[c['id'] for c in cases], required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--timeout', type=int, default=120)
    parser.add_argument('--skill', type=Path, default=SKILL,
                        help='Skill folder to evaluate, such as a frozen earlier version')
    parser.add_argument('--label', default='', help='Version label recorded and added to the filename')
    args = parser.parse_args()
    skill = args.skill.resolve()
    case = next(c for c in cases if c['id'] == args.case)
    args.output.mkdir(parents=True, exist_ok=True)
    record = {'host': args.host, 'arm': args.arm, 'case': args.case, 'label': args.label,
              'prompt': build_prompt(case, args.arm, args.host, skill), 'command': host_command(args.host, args.arm),
              'skill_hashes': {p.relative_to(skill).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in sorted(skill.rglob('*')) if p.is_file()},
              'missing_references': [r for r in case['references']
                                     if args.arm == 'references' and not (skill / 'references' / r).is_file()],
              'case_hash': hashlib.sha256(json.dumps(case, sort_keys=True).encode()).hexdigest()}
    stem = '-'.join(filter(None, (args.label, args.host, args.arm, args.case)))
    output = args.output / f'{stem}.json'
    if output.exists():
        parser.error(f'refusing to overwrite evaluation record: {output}')
    start = time.monotonic()
    try:
        record['host_version'] = subprocess.run([args.host, '--version'], capture_output=True,
                                                text=True, timeout=15).stdout.strip()
        with tempfile.TemporaryDirectory(prefix='quill-eval-') as tmp:
            project = Path(tmp)
            if args.arm in ('implicit', 'explicit'):
                directory = '.agents' if args.host == 'codex' else '.claude'
                shutil.copytree(skill, project / directory / 'skills/quill')
            for relative, content in case.get('files', {}).items():
                project.joinpath(relative).parent.mkdir(parents=True, exist_ok=True)
                project.joinpath(relative).write_text(content)
            completed = subprocess.run(record['command'], input=record['prompt'], cwd=project,
                                       capture_output=True, text=True, timeout=args.timeout)
            record.update(exit_code=completed.returncode, stdout=completed.stdout, stderr=completed.stderr)
            record['fixtures_unchanged'] = all(project.joinpath(p).is_file() and project.joinpath(p).read_text() == value
                                             for p, value in case.get('files', {}).items())
    except subprocess.TimeoutExpired as exc:
        def decoded(value):
            return value.decode(errors='replace') if isinstance(value, bytes) else value or ''
        record.update(error='host timeout', stdout=decoded(exc.stdout), stderr=decoded(exc.stderr))
    except OSError as exc:
        record['error'] = str(exc)
    record['elapsed_seconds'] = round(time.monotonic() - start, 2)
    output.write_text(json.dumps(record, indent=2) + '\n')
    print(output)
    if record.get('error') or record.get('exit_code') != 0:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
