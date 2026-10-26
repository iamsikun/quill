"""`quill check` and `quill review`: deterministic support for the writing review."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .check import check_file, format_result
from .review import ReviewStore, format_status
from .style import StyleStore, default_store


def run_check(args: argparse.Namespace) -> int:
    results = []
    for file in args.files:
        against = args.against
        if args.baseline:
            store = StyleStore(default_store(Path(file).resolve().parent))
            against = store.baseline_path(store.relative(file))
            if not against.is_file():
                raise ValueError(f'no baseline for {file}; run `quill style baseline` first')
        results.append(check_file(file, against, args.lines, profile=not args.no_profile))
    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print('\n'.join(format_result(r) for r in results), end='')
    found = any(r['style'] or r.get('fidelity') for r in results)
    return 1 if args.strict and found else 0


def run_review(args: argparse.Namespace) -> int:
    store = ReviewStore(args.store) if args.store else ReviewStore.for_project()
    if args.review_action == 'record':
        findings = Path(args.findings).read_text() if args.findings else ''
        for file in args.files:
            print(f'review recorded: {store.record(file, args.summary, findings)}')
        return 0
    result = store.status(args.files or None)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(format_status(result), end='')
    return 0 if all(info['state'] == 'current' for info in result.values()) else 1


def run_hook(args: argparse.Namespace) -> int:
    from .hooks import run
    output = run(args.hook_action, sys.stdin.read())
    if output:
        print(output)
    return 0


def add_parsers(subparsers) -> None:
    check = subparsers.add_parser('check', help='Report writing-review candidates and fidelity guards')
    check.add_argument('files', nargs='+', type=Path)
    source = check.add_mutually_exclusive_group()
    source.add_argument('--against', type=Path, help='Earlier version to compare for fidelity guards')
    source.add_argument('--baseline', action='store_true', help="Compare with Quill's style baseline")
    check.add_argument('--lines', action='append', default=[], metavar='A-B',
                       help='Authorized line span in the current file; repeatable')
    check.add_argument('--no-profile', action='store_true', help="Ignore the profiles' lint patterns")
    check.add_argument('--json', action='store_true', help='Machine-readable output')
    check.add_argument('--strict', action='store_true', help='Exit 1 when anything is reported')
    check.set_defaults(func=run_check)

    review = subparsers.add_parser('review', help='Record and check which file versions passed the review')
    actions = review.add_subparsers(dest='review_action', required=True)
    record = actions.add_parser('record', help='Record the current files as reviewed')
    record.add_argument('files', nargs='+', type=Path)
    record.add_argument('--summary', default='', help='One-line summary of the review')
    record.add_argument('--findings', type=Path, help='File with the review findings to keep')
    status = actions.add_parser('status', help='Report whether files still match their last review')
    status.add_argument('files', nargs='*', type=Path, help='Default: every reviewed file')
    status.add_argument('--json', action='store_true', help='Machine-readable output')
    for action in (record, status):
        action.add_argument('--store', type=Path, help='Review folder; default: nearest project .quill/reviews')
        action.set_defaults(func=run_review)

    hook = subparsers.add_parser('hook', help='Opt-in Claude Code hooks for the writing review')
    hook.add_argument('hook_action', choices=('post-edit', 'stop'))
    hook.set_defaults(func=run_hook)
