"""`quill style`: track Quill's last version of a file and show the author's later edits."""
from __future__ import annotations

import argparse
from pathlib import Path

from .style import StyleStore, default_store, format_changes


def run(args: argparse.Namespace) -> int:
    store = StyleStore(args.store or default_store())
    if args.style_action == 'baseline':
        for file in args.files:
            print(f'baseline saved: {store.baseline(file)}')
    else:
        print(format_changes(store.changes(args.files or None)), end='')
    return 0


def add_parser(subparsers) -> None:
    parser = subparsers.add_parser('style', help='Track edits to Quill-written files for personal writing memory')
    actions = parser.add_subparsers(dest='style_action', required=True)
    baseline = actions.add_parser('baseline', help="Record files as Quill's last version")
    baseline.add_argument('files', nargs='+', type=Path)
    changes = actions.add_parser('changes', help="Show paragraphs changed since Quill's last version")
    changes.add_argument('files', nargs='*', type=Path, help='Default: every file with a baseline')
    for action in (baseline, changes):
        action.add_argument('--store', type=Path, help='Memory folder; default: nearest project .quill/style')
        action.set_defaults(func=run)
