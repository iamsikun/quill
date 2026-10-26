"""Blind model grading for evaluation records, with labels revealed only afterwards.

`cases` grades single-turn records from run.py: all answers to one case are shuffled,
relabeled, and graded together against the frozen rubric. `session` grades one
session.py record at a time, without its arm, skill, trace, or tool evidence.
Model judgments are preliminary evidence, not a substitute for human review.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import random
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'evals'))
from personalization import final_text  # noqa: E402

GRADER = ['claude', '-p', '--safe-mode', '--disable-slash-commands', '--tools', '', '--no-session-persistence',
          '--strict-mcp-config', '--mcp-config', '{"mcpServers":{}}', '--output-format', 'stream-json', '--verbose']


def ask(prompt: str, timeout: int) -> dict:
    done = subprocess.run(GRADER, input=prompt, capture_output=True, text=True, timeout=timeout)
    text = final_text(done.stdout)
    match = re.search(r'\{.*\}', text, re.S)
    if done.returncode or not match:
        raise RuntimeError(f'grader failed: {done.stderr[-500:]} {text[:500]}')
    return json.loads(match.group(0))


def grade_cases(records: list[Path], seed: int, timeout: int) -> dict:
    cases = {c['id']: c for c in json.loads((ROOT / 'evals/cases.json').read_text())}
    rubric = (ROOT / 'evals/rubrics/cases.md').read_text()
    by_case: dict[str, list[dict]] = {}
    for path in records:
        record = json.loads(path.read_text())
        by_case.setdefault(record['case'], []).append(
            {'record': path.name, 'answer': final_text(record.get('stdout', '')), 'failed': bool(record.get('error'))})
    rng = random.Random(seed)
    results = {}
    for case_id, answers in sorted(by_case.items()):
        case = cases[case_id]
        rng.shuffle(answers)
        for index, answer in enumerate(answers):
            answer['label'] = f'answer-{index + 1}'
        blocks = '\n\n'.join(f"### {a['label']}\n{a['answer'] or '(no answer: host failure)'}" for a in answers)
        fields = {k: case[k] for k in ('must_preserve', 'must_not', 'rhetorical_checks') if k in case}
        prompt = (f"{rubric}\n\n## Task\n{case['prompt']}\n\n## Source\n{case['source']}\n\n"
                  f"## Grading fields\n{json.dumps(fields, indent=1)}\n\n## Answers\n{blocks}")
        graded = ask(prompt, timeout)['answers']
        by_label = {g['label']: g for g in graded}
        results[case_id] = [{**by_label.get(a['label'], {'error': 'not graded'}), 'record': a['record'],
                             'host_failed': a['failed']} for a in answers]
        print(case_id, [(r['record'], r.get('fidelity'), r.get('effort')) for r in results[case_id]], flush=True)
    return results


def grade_session(record_path: Path, timeout: int) -> dict:
    record = json.loads(record_path.read_text())
    case_dir = ROOT / 'evals/sessions' / record['case']
    case = json.loads((case_dir / 'session.json').read_text())
    rubric = (ROOT / 'evals/rubrics/session.md').read_text()
    turns = []
    for turn in record['turns']:
        request = next(t['prompt'] for t in case['turns'] if t['id'] == turn['turn'])
        turns.append(f"### {turn['turn']}\nUser: {request}\n\nAssistant reply:\n{turn.get('reply', '')}\n\n"
                     f"Manuscript after {turn['turn']}:\n```markdown\n{turn['manuscript']}\n```")
    prompt = (f"{rubric}\n\n## Embedded failures\n{json.dumps(case['failures'], indent=1)}\n\n"
              f"## Code notes supplied to the assistant\n{(case_dir / 'CODE.md').read_text()}\n\n"
              f"## Original manuscript\n```markdown\n{(case_dir / 'paper.md').read_text()}\n```\n\n"
              f"## Turns\n" + '\n\n'.join(turns))
    return ask(prompt, timeout)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('kind', choices=('cases', 'session'))
    parser.add_argument('records', nargs='+', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--seed', type=int, default=20261026)
    parser.add_argument('--timeout', type=int, default=1500)
    parser.add_argument('--jobs', type=int, default=3, help='Sessions graded in parallel')
    args = parser.parse_args()
    if args.kind == 'cases':
        if args.output.exists():
            parser.error(f'refusing to overwrite grades: {args.output}')
        result = grade_cases(args.records, args.seed, args.timeout)
        args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    else:
        # Session grades are saved as each finishes; rerunning grades only what is missing.
        result = json.loads(args.output.read_text()) if args.output.exists() else {}
        todo = [p for p in args.records if 'error' in result.get(p.name, {'error': 'missing'})]

        def one(path: Path) -> tuple[str, dict]:
            for attempt in range(2):
                try:
                    return path.name, grade_session(path, args.timeout)
                except (RuntimeError, ValueError, subprocess.TimeoutExpired) as exc:
                    error = f'{type(exc).__name__}: {str(exc)[:300]}'
            return path.name, {'error': error}

        with ThreadPoolExecutor(args.jobs) as pool:
            for name, grade in pool.map(one, todo):
                result[name] = grade
                args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
                print(name, 'error' if 'error' in grade else 'graded', flush=True)
    print(args.output)


if __name__ == '__main__':
    main()
