"""Isolated, fresh-session inference/apply comparison for portable writing memory.

The runner persists model-proposed updates between sessions; it does not test host
skill discovery or automatic file-tool use. Every model session remains read-only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile
import time

from quill.style import StyleStore, export_context, writing_context

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills/quill'
ARMS = ('none', 'static', 'learned', 'examples')


def training_prompt(case: dict) -> str:
    references = '\n\n'.join((SKILL / 'references' / name).read_text() for name in
                              ('personalization.md', 'personalization-format.md'))
    return '\n\n'.join([
        'This is an isolated simulated-author evaluation. No external tools, files, or services. '
        'Return only a JSON object with evidence and preferences lists in the record input format. '
        'The harness will persist it to an empty learn-mode store. Infer only useful, justified lessons. '
        'Keep the response under 2000 words. Do not include commentary or Markdown fences.',
        (SKILL / 'SKILL.md').read_text(), references,
        'Shared fixture-project scope vocabulary: section=introduction, methods, results, '
        'executive-summary, proof; audience=economics (economists), managers, mathematical; '
        'decision=framing, definition, copyediting. Reuse these tags when appropriate; '
        'other scopes may use descriptive tags. This vocabulary is the same in every case.',
        'Author feedback and source context:\n' + case['training'],
    ])


def application_prompt(case: dict, memory: str = '') -> str:
    parts = ['Complete the writing task in at most 350 words. Do not use tools or access external services. '
             'All permitted context is included below.', (SKILL / 'SKILL.md').read_text()]
    if memory:
        parts.append('Applicable writing memory (examples do not establish research findings):\n' + memory)
    parts += [case['request'], 'Source material:\n' + case['source']]
    return '\n\n'.join(parts)


def command(host: str) -> list[str]:
    if host == 'codex':
        return ['codex', 'exec', '--ephemeral', '--skip-git-repo-check', '--sandbox', 'read-only', '--json', '-']
    return ['claude', '-p', '--no-session-persistence', '--output-format', 'stream-json', '--verbose',
            '--strict-mcp-config', '--mcp-config', '{"mcpServers":{}}', '--safe-mode',
            '--disable-slash-commands', '--tools', '']


def final_text(stdout: str) -> str:
    texts = []
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get('type') == 'result' and isinstance(event.get('result'), str):
            return event['result']
        item = event.get('item', {})
        if event.get('type') == 'item.completed' and item.get('type') == 'agent_message':
            texts.append(item['text'])
        if event.get('type') == 'assistant':
            texts += [part['text'] for part in event.get('message', {}).get('content', [])
                      if part.get('type') == 'text']
    return texts[-1].strip() if texts else ''


def invoke(host: str, prompt: str, project: Path, timeout: int) -> dict:
    start = time.monotonic()
    argv = command(host)
    try:
        completed = subprocess.run(argv, cwd=project, input=prompt, text=True,
                                   capture_output=True, timeout=timeout)
        return {'prompt': prompt, 'command': argv, 'stdout': completed.stdout, 'stderr': completed.stderr,
                'exit_code': completed.returncode, 'text': final_text(completed.stdout),
                'elapsed_seconds': round(time.monotonic() - start, 2)}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {'prompt': prompt, 'command': argv, 'error': str(exc),
                'elapsed_seconds': round(time.monotonic() - start, 2)}


def run_case(case: dict, host: str, arm: str, timeout: int, training_record: dict | None = None) -> dict:
    record = {'host': host, 'arm': arm, 'case': case['id'], 'stages': [],
              'case_hash': hashlib.sha256(json.dumps(case, sort_keys=True).encode()).hexdigest(),
              'skill_hashes': {p.relative_to(SKILL).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in sorted(SKILL.rglob('*')) if p.is_file()},
              'limitation': 'Harness-managed persistence; not an automatic invocation test.'}
    try:
        record['host_version'] = subprocess.run([host, '--version'], capture_output=True, text=True,
                                                timeout=15).stdout.strip()
    except (OSError, subprocess.TimeoutExpired) as exc:
        record['error'] = str(exc)
        return record
    with tempfile.TemporaryDirectory(prefix='quill-personalization-') as temporary:
        project = Path(temporary)
        memory = ''
        if arm == 'static':
            memory = (SKILL / 'references/author-style.md').read_text()
        if arm in ('learned', 'examples') and case.get('storage_available', True):
            if training_record is not None:
                if any(training_record.get(key) != record[key] for key in ('case_hash', 'skill_hashes', 'host')):
                    record['error'] = 'Training record does not match the case, skill, and host'
                    return record
                if training_record.get('arm') not in ('learned', 'examples') or not training_record.get('stages'):
                    record['error'] = 'Training record has no learning stage'
                    return record
                training = training_record['stages'][0]
                record['training_reused'] = True
            else:
                training = invoke(host, training_prompt(case), project, timeout)
            record['stages'].append(training)
            if training.get('exit_code') != 0:
                record['error'] = 'Training host failed or timed out'
                return record
            try:
                raw = re.sub(r'^```(?:json)?\s*|\s*```$', '', training['text']).strip()
                proposal = json.loads(raw)
                store = StyleStore(project / '.quill/style')
                store.init('learn')
                store.record(0, proposal)
                record['memory'] = store.show()
                # Reopen the saved store for the independent application session.
                context = writing_context(StyleStore(store.path), case['scope'],
                                          examples=3 if arm == 'examples' else 0)
                memory = export_context(context)
                record['context'] = context
            except (ValueError, KeyError, TypeError, OSError) as exc:
                record['error'] = 'Invalid learning update: ' + str(exc)
                return record
        if not case.get('storage_available', True):
            memory = 'Current-conversation feedback only; not saved:\n' + case['training']
        application = invoke(host, application_prompt(case, memory), project, timeout)
        record['stages'].append(application)
        if application.get('exit_code') != 0 or not application.get('text'):
            record['error'] = 'Application host failed, timed out, or returned no text'
    return record


def main() -> None:
    cases = json.loads(Path(__file__).with_name('personalization.json').read_text())
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', choices=('codex', 'claude'), required=True)
    parser.add_argument('--arm', choices=ARMS, required=True)
    parser.add_argument('--case', choices=[c['id'] for c in cases], required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--timeout', type=int, default=180)
    parser.add_argument('--training-record', type=Path,
                        help='Reuse matching learned/examples evidence to isolate the effect of retrieved examples')
    args = parser.parse_args()
    destination = args.output / f'{args.host}-{args.arm}-{args.case}.json'
    if destination.exists():
        parser.error('refusing to overwrite an evaluation record')
    case = next(c for c in cases if c['id'] == args.case)
    if args.training_record and args.arm not in ('learned', 'examples'):
        parser.error('--training-record requires a learned or examples arm')
    training = json.loads(args.training_record.read_text()) if args.training_record else None
    record = run_case(case, args.host, args.arm, args.timeout, training)
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation also protects concurrent evaluation runs.
    with destination.open('x') as stream:
        json.dump(record, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(destination)
    if record.get('error'):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
