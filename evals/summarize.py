"""Tabulate graded single-turn cases and session records by version, arm, and failure type."""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from session import SESSIONS, control_results  # noqa: E402


def controls_of(record: dict) -> dict[str, bool]:
    """Recompute controls from the saved final text with the current definitions."""
    case_dir = SESSIONS / record['case']
    case = json.loads((case_dir / 'session.json').read_text())
    return control_results(case['controls'], (case_dir / 'paper.md').read_text(), record['final'])


def group_of(record: str) -> str:
    """`before-claude-core-case.json` -> `before/core`."""
    label, _host, arm = record.split('-')[:3]
    return f'{label}/{arm}'


def resolved(status: str | None) -> bool:
    """`fixed`, `found`, or a combined `found; fixed`; never `partial`, `missed`, or `not fixed`."""
    status = (status or '').lower()
    return ('fixed' in status or 'found' in status) and not any(
        word in status for word in ('not fixed', 'missed', 'partial', 'worse'))


def arm_table(grades: dict) -> str:
    """Session grades pooled by host and arm."""
    rows = defaultdict(list)
    for name, grade in grades.items():
        if 'error' not in grade:
            host, arm = name.split('-')[:2]
            rows[f'{host} {arm}'].append(grade)
    lines = ['| Host and arm | Sessions | Failures fixed or found | Fidelity errors | New defects | Over-corrections | Replies fitting the request | Continuity | Contribution clarity | Author effort |',
             '|---|---|---|---|---|---|---|---|---|---|']
    for key, grades_ in sorted(rows.items()):
        count = lambda field: sum(len(g[field]) for g in grades_)
        good = sum(resolved(f.get('status')) for g in grades_ for f in g['failures'].values())
        total = sum(len(g['failures']) for g in grades_)
        fitting = sum(v == 2 for g in grades_ for v in g['reply_discipline'].values())
        turns = sum(len(g['reply_discipline']) for g in grades_)
        mean = lambda field: sum(g[field] for g in grades_) / len(grades_)
        lines.append(f"| {key} | {len(grades_)} | {good}/{total} | {count('fidelity_errors')} | {count('new_defects')} | "
                     f"{count('overcorrection')} | {fitting}/{turns} | {mean('continuity'):.2f} | "
                     f"{mean('contribution_clarity'):.2f} | {mean('author_effort'):.2f} |")
    return '\n'.join(lines)


def cases_table(grades: dict) -> str:
    rows = defaultdict(lambda: defaultdict(int))
    for answers in grades.values():
        for answer in answers:
            if answer.get('host_failed') or 'fidelity' not in answer:
                rows[group_of(answer['record'])]['incomplete'] += 1
                continue
            row = rows[group_of(answer['record'])]
            row['n'] += 1
            row['fidelity'] += answer['fidelity'] == 'pass'
            row['scope'] += answer['scope'] == 'pass'
            row['discipline2'] += answer['discipline'] == 2
            row['effort'] += answer['effort']
            for check in answer.get('checks', []):
                row['checks'] += 1
                row['met'] += check == 'met'
    lines = ['| Version/arm | Answers | Fidelity pass | Scope pass | Discipline 2 | Rhetorical checks met | Mean effort |',
             '|---|---|---|---|---|---|---|']
    for group, r in sorted(rows.items()):
        n = r['n'] or 1
        lines.append(f"| {group} | {r['n']} | {r['fidelity']}/{r['n']} | {r['scope']}/{r['n']} | "
                     f"{r['discipline2']}/{r['n']} | {r['met']}/{r['checks']} | {r['effort'] / n:.2f} |")
    return '\n'.join(lines)


def per_case(grades: dict) -> str:
    lines = ['| Case | before/core | after/core | before/references | after/references | none/plain |', '|---|---|---|---|---|---|']
    for case, answers in sorted(grades.items()):
        cells = {}
        for a in answers:
            if 'fidelity' in a:
                met = sum(c == 'met' for c in a.get('checks', []))
                cells[group_of(a['record'])] = f"{'F' if a['fidelity'] == 'pass' else 'x'} {met}/{len(a.get('checks', []))} e{a['effort']}"
        if any(k.startswith(('before', 'after')) for k in cells):
            lines.append(f"| {case} | " + ' | '.join(cells.get(k, '–') for k in (
                'before/core', 'after/core', 'before/references', 'after/references', 'none/plain')) + ' |')
    return '\n'.join(lines)


def session_table(records: list[Path], grades: dict) -> str:
    lines = ['| Record | Turns done | Skill files read (turn 1 / later) | Subagent calls | CLI calls | Out-of-scope edits | Review-only unchanged | Controls kept | Copy current | Failures fixed or found | Fidelity errors | New defects | Over-correction | Continuity | Clarity | Effort |',
             '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|']
    for path in records:
        r = json.loads(path.read_text())
        g = grades.get(path.name, {})
        turns = r['turns']
        first = len(turns[0]['summary']['skill_files_read']) if turns else 0
        later = sorted({f for t in turns[1:] for f in t['summary']['skill_files_read']})
        statuses = [v.get('status') for v in g.get('failures', {}).values()]
        good = sum(resolved(s) for s in statuses)
        scope = sum(bool(t['checks']['out_of_scope_changes']) for t in turns)
        review = next((t['checks'].get('files_unchanged') for t in turns if 'files_unchanged' in t['checks']), None)
        r['controls'] = controls_of(r)
        controls = sum(r['controls'].values())
        lost = ', '.join(k.split('-')[0] for k, v in r['controls'].items() if not v) or 'none'
        lines.append(
            f"| {path.stem} | {len(turns)} | {first} / {len(later)} | {sum(t['summary']['subagent_calls'] for t in turns)} | "
            f"{len([e for e in r.get('cli_events', []) if not e.get('unavailable')])} | {scope} turn(s) | {review} | "
            f"{controls}/{len(r['controls'])} ({lost}) | {r['delivered_copy_current']} | {good}/{len(statuses)} | "
            f"{len(g.get('fidelity_errors', []))} | {len(g.get('new_defects', []))} | {len(g.get('overcorrection', []))} | "
            f"{g.get('continuity', '–')} | {g.get('contribution_clarity', '–')} | {g.get('author_effort', '–')} |")
    return '\n'.join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case-grades', type=Path)
    parser.add_argument('--sessions', type=Path, nargs='*', default=[])
    parser.add_argument('--session-grades', type=Path)
    args = parser.parse_args()
    if args.case_grades:
        grades = json.loads(args.case_grades.read_text())
        print(cases_table(grades), '\n')
        print(per_case(grades), '\n')
    if args.sessions:
        grades = json.loads(args.session_grades.read_text()) if args.session_grades else {}
        records = sorted(args.sessions, key=lambda p: re.sub(r'\d+', lambda m: m.group().zfill(3), p.name))
        print(session_table(records, grades), '\n')
        if grades:
            print(arm_table(grades))


if __name__ == '__main__':
    main()
