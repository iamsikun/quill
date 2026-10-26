"""Run a multi-turn manuscript revision in one host session with file tools and traces.

Arms are frozen skill versions and review configurations (issue #6):

- A: the supplied skill (the baseline), writer only.
- B: A plus one instruction to review and revise twice against the guidance.
- C: the supplied skill (the structured review protocol), writer only.
- D: C with the host's subagent tool, so an independent reviewer is possible.
- E: D with the `quill` CLI on PATH for `quill check` and review records.
- F: E with Quill's opt-in Claude Code hooks (`quill hook post-edit` and `stop`).

The runner copies the fixture into a disposable project, installs the skill there,
and isolates XDG_CONFIG_HOME so no personal writing profile is visible. It records
prompts, replies, tool traces, the manuscript after every turn, and deterministic
checks. Grading fields in the session file never enter prompts.
"""
from __future__ import annotations

import argparse
import difflib
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
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from host_memory import tool_trace  # noqa: E402
from personalization import final_text  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SESSIONS = ROOT / 'evals/sessions'
ARMS = ('A', 'B', 'C', 'D', 'E', 'F')
HOOKS = {'hooks': {
    'PostToolUse': [{'matcher': 'Edit|Write', 'hooks': [{'type': 'command', 'command': 'quill hook post-edit'}]}],
    'Stop': [{'hooks': [{'type': 'command', 'command': 'quill hook stop'}]}]}}
TWICE = ('\n\nBefore delivering any substantial writing, review it against this skill\'s guidance '
         'twice and revise it each time.\n')
SETUP = ('This is a disposable synthetic manuscript in the current folder. Work in the actual files. '
         'There is no writing profile for this task: do not read personal files or memory outside this '
         'folder, use connected services, or change settings or installed tools.')
NUMBER = re.compile(r'(?<![A-Za-z\\_])\d+(?:\.\d+)?')


def sections(text: str) -> dict[str, str]:
    """Top-level parts keyed by their `## ` heading; the title block is keyed ''."""
    parts, key, current = {}, '', []
    for line in text.splitlines(keepends=True):
        if line.startswith('## '):
            parts[key] = ''.join(current)
            key, current = line.strip(), []
        current.append(line)
    parts[key] = ''.join(current)
    return parts


def section_like(parts: dict[str, str], heading: str) -> str | None:
    """Match a heading even if a revision renamed it, by its number or first word."""
    if heading in parts:
        return parts[heading]
    stem = heading.split('.')[0] if heading[3:4].isdigit() else ' '.join(heading.split()[:2])
    return next((text for key, text in parts.items() if key.startswith(stem)), None)


def out_of_scope_changes(before: str, after: str, scope: list[str]) -> list[str]:
    old, new = sections(before), sections(after)
    changed = []
    for key, text in old.items():
        if any(key == s or (s[3:4].isdigit() and key.startswith(s.split('.')[0])) for s in scope):
            continue
        if section_like(new, key) != text:
            changed.append(key or '(title)')
    return changed


def control_results(controls: list[dict], original: str, final: str) -> dict[str, bool]:
    results = {}
    for control in controls:
        text = final
        if 'section' in control:
            text = section_like(sections(final), control['section']) or ''
        if 'verbatim' in control:
            ok = control['verbatim'] in text
        elif 'verbatim_lines' in control:
            ok = all(line in text.splitlines() for line in control['verbatim_lines'])
        elif 'sentence_with' in control:
            sentences = re.split(r'(?<=[.!?])\s+', text)
            ok = any(all(token in sentence for token in control['sentence_with']) for sentence in sentences)
        elif 'any' in control:
            ok = any(token in text for token in control['any'])
        elif 'all' in control:
            ok = all(token in text for token in control['all'])
        elif 'similar_to' in control:
            target = control['similar_to']
            best = max((difflib.SequenceMatcher(None, target, p).ratio() for p in text.split('\n\n')), default=0)
            ok = best >= control['min_ratio']
        elif 'section_unchanged' in control:
            ok = section_like(sections(final), control['section_unchanged']) == sections(original)[control['section_unchanged']]
        elif control.get('numbers_kept'):
            ok = set(NUMBER.findall(original)) <= set(NUMBER.findall(final))
            if not ok:
                control['missing'] = sorted(set(NUMBER.findall(original)) - set(NUMBER.findall(final)))
        results[control['id']] = ok
    return results


def trace_summary(trace: list[dict]) -> dict:
    reads, subagents, cli, profile = set(), 0, [], False
    for event in trace:
        blob = json.dumps(event.get('input') or event.get('tool_input') or event.get('command', ''))
        name = event.get('name') or event.get('tool_name') or event.get('type')
        for match in re.findall(r'skills/quill/((?:references/)?[\w.-]+\.md)', blob):
            if name in ('Read', 'command_execution', 'Bash', 'Skill'):
                reads.add(match)
        if name == 'Skill':
            reads.add('SKILL.md')
        if name in ('Agent', 'Task') and event.get('type') == 'tool_use':
            subagents += 1
        for command in re.findall(r'quill (?:check|review|style)[^"\\]*', blob):
            cli.append(command.strip())
        if '.config/quill' in blob:
            profile = True
    return {'skill_files_read': sorted(reads), 'subagent_calls': subagents,
            'quill_cli_calls': sorted(set(cli)), 'personal_profile_touched': profile}


def host_commands(host: str, arm: str, session: str | None, first: bool, config: Path) -> list[str]:
    if host == 'codex':
        base = ['codex', 'exec']
        if not first:
            base += ['resume', session]
        return base + ['--json', '--skip-git-repo-check', '--ignore-user-config',
                       '-c', 'sandbox_mode="workspace-write"', '-c', 'approval_policy="never"', '-']
    tools = ['Read', 'Edit', 'Write', 'Glob', 'Grep', 'Bash', 'Skill'] + (['Agent'] if arm in 'DEF' else [])
    settings = json.dumps(HOOKS) if arm == 'F' else '{"disableAllHooks":true}'
    command = ['claude', '-p', '--output-format', 'stream-json', '--verbose', '--restricted',
               '--setting-sources', 'project', '--strict-mcp-config', '--mcp-config', '{"mcpServers":{}}',
               '--settings', settings, '--permission-mode', 'dontAsk',
               '--tools', ','.join(tools), '--allowedTools', *tools]
    command += ['--session-id', session] if first else ['--resume', session]
    return command + ['--']


def codex_thread(stdout: str) -> str | None:
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get('type') == 'thread.started':
            return event.get('thread_id')
    return None


def model_of(stdout: str) -> str | None:
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get('type') == 'system' and event.get('model'):
            return event['model']
    return None


def prepare(root: Path, case_dir: Path, case: dict, host: str, arm: str, skill: Path) -> tuple[Path, Path]:
    project, config = root / 'project', root / 'config'
    project.mkdir()
    for relative in case['files']:
        shutil.copy2(case_dir / relative, project / relative)
    subprocess.run([sys.executable, 'render.py'], cwd=project, check=True, capture_output=True)
    delivered = case['delivered']
    (project / delivered['copy']).parent.mkdir(parents=True, exist_ok=True)
    shutil.move(project / delivered['build'], project / delivered['copy'])
    shutil.rmtree(project / 'build', ignore_errors=True)
    target = project / ('.agents' if host == 'codex' else '.claude') / 'skills/quill'
    shutil.copytree(skill, target)
    if arm == 'B':
        with (target / 'SKILL.md').open('a') as stream:
            stream.write(TWICE)
    (config / 'bin').mkdir(parents=True)
    wrapper = config / 'bin/quill'
    # Arms without the CLI get a stub that shadows any installed `quill` and logs attempts.
    available = 'True' if arm in 'EF' else 'False'
    wrapper.write_text(f'''#!{sys.executable}
import json, os, subprocess, sys
if not {available}:
    with open({str(config / 'cli-events.jsonl')!r}, 'a') as stream:
        stream.write(json.dumps(dict(turn=os.environ.get('QUILL_EVAL_TURN'), args=sys.argv[1:],
                                     exit_code=127, unavailable=True)) + '\\n')
    sys.stderr.write('quill: command not found\\n')
    sys.exit(127)
env = dict(os.environ, PYTHONPATH={str(ROOT / 'src')!r})
run = subprocess.run([{sys.executable!r}, '-m', 'quill', *sys.argv[1:]], capture_output=True, text=True, env=env)
with open({str(config / 'cli-events.jsonl')!r}, 'a') as stream:
    stream.write(json.dumps(dict(turn=os.environ.get('QUILL_EVAL_TURN'), args=sys.argv[1:],
                                 exit_code=run.returncode)) + '\\n')
sys.stdout.write(run.stdout)
sys.stderr.write(run.stderr)
sys.exit(run.returncode)
''')
    wrapper.chmod(0o755)
    subprocess.run(['git', 'init', '-q'], cwd=project, check=True)
    return project, config


def run_session(case_dir: Path, host: str, arm: str, skill: Path, timeout: int) -> dict:
    case = json.loads((case_dir / 'session.json').read_text())
    original = (case_dir / 'paper.md').read_text()
    record = {'case': case['id'], 'host': host, 'arm': arm, 'skill': str(skill), 'turns': [],
              'skill_hashes': {p.relative_to(skill).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in sorted(skill.rglob('*')) if p.is_file()},
              'host_version': subprocess.run([host, '--version'], capture_output=True, text=True,
                                             timeout=30).stdout.strip()}
    with tempfile.TemporaryDirectory(prefix='quill-session-') as tmp:
        root = Path(tmp).resolve()
        project, config = prepare(root, case_dir, case, host, arm, skill)
        env = dict(os.environ, XDG_CONFIG_HOME=str(config),
                   PATH=str(config / 'bin') + os.pathsep + os.environ['PATH'])
        session = str(uuid.uuid4()) if host == 'claude' else None
        # Print-mode hosts do not reliably expose project skills as commands, so the first
        # request names the skill file. Later requests rely on the session retaining it.
        skill_file = ('.agents' if host == 'codex' else '.claude') + '/skills/quill/SKILL.md'
        invoke = f'Use the Quill writing skill in {skill_file} for this session. '
        for index, turn in enumerate(case['turns']):
            before = (project / 'paper.md').read_text()
            prompt = turn['prompt'] if index else f"{invoke}{turn['prompt']}\n\n{SETUP}"
            command = host_commands(host, arm, session, index == 0, config)
            item = {'turn': turn['id'], 'prompt': prompt, 'command': command}
            start = time.monotonic()
            try:
                done = subprocess.run(command, input=prompt, cwd=project, capture_output=True, text=True,
                                      timeout=timeout, env=dict(env, QUILL_EVAL_TURN=turn['id']))
                item.update(exit_code=done.returncode, reply=final_text(done.stdout),
                            trace=tool_trace(done.stdout), stderr=done.stderr[-4000:])
                record.setdefault('model', model_of(done.stdout))
                if host == 'codex' and index == 0:
                    session = codex_thread(done.stdout)
            except subprocess.TimeoutExpired as exc:
                stdout = exc.stdout.decode(errors='replace') if isinstance(exc.stdout, bytes) else exc.stdout or ''
                item.update(error='host timeout', reply=final_text(stdout), trace=tool_trace(stdout))
            item['elapsed_seconds'] = round(time.monotonic() - start, 2)
            after = (project / 'paper.md').read_text()
            item['manuscript'] = after
            item['summary'] = trace_summary(item.get('trace', []))
            if index == 0:
                record['skill_loaded'] = 'SKILL.md' in item['summary']['skill_files_read']
            item['checks'] = {'out_of_scope_changes': out_of_scope_changes(before, after, turn['scope'])}
            if turn.get('review_only'):
                item['checks']['files_unchanged'] = before == after
            record['turns'].append(item)
            print(f"{host} {arm} {turn['id']}: {item['elapsed_seconds']}s {item['checks']} "
                  f"{item['summary']}", flush=True)
            if item.get('error') or item.get('exit_code') != 0 or (host == 'codex' and not session):
                record['error'] = f"{turn['id']}: host failed"
                break
        final = (project / 'paper.md').read_text()
        record['final'] = final
        record['controls'] = control_results(case['controls'], original, final)
        delivered = case['delivered']
        check = root / 'render-check'
        check.mkdir()
        shutil.copy2(project / 'paper.md', check / 'paper.md')
        shutil.copy2(case_dir / 'render.py', check / 'render.py')
        subprocess.run([sys.executable, 'render.py'], cwd=check, check=True, capture_output=True)
        copy = project / delivered['copy']
        record['other_files_changed'] = sorted(
            relative for relative in case['files'] if relative != delivered['source']
            and (project / relative).read_bytes() != (case_dir / relative).read_bytes())
        record['delivered_copy_current'] = copy.is_file() and copy.read_bytes() == (check / delivered['build']).read_bytes()
        events = config / 'cli-events.jsonl'
        record['cli_events'] = [json.loads(l) for l in events.read_text().splitlines()] if events.exists() else []
        review_dir = project / '.quill/reviews'
        record['review_records'] = sorted(p.name for p in review_dir.rglob('*.json')) if review_dir.is_dir() else []
        encoded = json.dumps(record).replace(str(root), '<fixture>').replace(str(ROOT), '<checkout>')
        return json.loads(encoded.replace(str(Path.home()), '<home>'))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--host', choices=('codex', 'claude'), required=True)
    parser.add_argument('--arm', choices=ARMS, required=True)
    parser.add_argument('--skill', type=Path, required=True, help='Frozen skill folder for this arm')
    parser.add_argument('--case', default='creative-selection')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--timeout', type=int, default=1200, help='Seconds per turn')
    args = parser.parse_args()
    if args.output.exists():
        parser.error(f'refusing to overwrite evaluation record: {args.output}')
    record = run_session(SESSIONS / args.case, args.host, args.arm, args.skill.resolve(), args.timeout)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as stream:
        json.dump(record, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(args.output)
    if record.get('error'):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
