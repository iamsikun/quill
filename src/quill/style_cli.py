"""Agent-facing deterministic helpers for the portable personalization workflow."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .style import MODES, SCOPE_KEYS, StyleStore, author_store, default_store, export_context, writing_context


def _input(path: str) -> bytes:
    return sys.stdin.buffer.read() if path == '-' else Path(path).read_bytes()


def _source(store: StyleStore, file: str) -> str:
    """Project-relative path, so moving or cloning a project keeps its baselines."""
    path = Path(file).resolve()
    if store.path.parent.name == '.quill':
        try:
            return path.relative_to(store.path.parent.parent).as_posix()
        except ValueError:
            pass
    return str(path)


def run(args: argparse.Namespace) -> int:
    store = StyleStore(args.store or default_store())
    action = args.style_action
    if action == 'init':
        linked = Path(args.author_store).expanduser() if args.author_store else None
        if args.author:
            linked = author_store(args.author)
            author = StyleStore(linked)
            if not author.path.exists():
                author.init(args.mode)
            else:
                author.load()
        result = store.init(args.mode, linked)
    elif action == 'configure':
        result = store.configure(args.expected_revision, args.mode,
                                 Path(args.author_store).expanduser() if args.author_store else None,
                                 args.unlink_author, args.revision_author, args.no_revision_author)
    elif action in ('snapshot', 'harvest'):
        if args.file == '-' and not args.source:
            raise ValueError('--source is required for a passage supplied on stdin')
        source = args.source or _source(store, args.file)
        raw = _input(args.file)
        if action == 'snapshot':
            result = store.snapshot(args.expected_revision, source, raw)
        else:
            result = store.harvest(source, raw, args.baseline)
    elif action == 'record':
        result = store.record(args.expected_revision, json.loads(_input(args.input)),
                              args.profile_hash, args.author_request)
    elif action == 'show':
        result = store.show(args.id)
    elif action == 'history':
        result = {'store': str(store.path), 'history': store.history()}
    elif action == 'restore':
        result = store.restore(args.expected_revision, args.version)
    elif action == 'forget':
        result = store.forget(args.expected_revision, args.id)
    elif action == 'promote':
        result = store.promote(args.expected_revision, args.id, args.author_revision)
    else:
        query = {key: getattr(args, key) for key in SCOPE_KEYS if getattr(args, key)}
        result = writing_context(store, query, args.budget, args.examples)
        if action == 'export':
            print(export_context(result), end='')
            return 0
    # JSON output: agents can use exact IDs and revisions without parsing prose.
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def add_parser(subparsers) -> None:
    parser = subparsers.add_parser('style', help='Inspect and maintain optional personal writing memory')
    actions = parser.add_subparsers(dest='style_action', required=True)
    for name in ('init', 'configure', 'snapshot', 'harvest', 'record', 'context', 'show',
                 'history', 'restore', 'forget', 'promote', 'export'):
        action = actions.add_parser(name)
        action.add_argument('--store', type=Path, help='Explicit store; default: nearest project .quill/style')
        if name in ('configure', 'snapshot', 'record', 'restore', 'forget', 'promote'):
            action.add_argument('--expected-revision', type=int, required=True,
                                help='Revision returned by show/context; stale updates are rejected')
        if name in ('init', 'configure'):
            action.add_argument('--mode', choices=MODES, default='off' if name == 'init' else None)
            links = action.add_mutually_exclusive_group()
            links.add_argument('--author-store', help='Link an existing author store without copying it')
            if name == 'init':
                links.add_argument('--author', help='Create or link an author in the configured author directory')
            else:
                links.add_argument('--unlink-author', action='store_true')
                attribution = action.add_mutually_exclusive_group()
                attribution.add_argument('--revision-author',
                                         help='Author declared to make the edits found between agent writes')
                attribution.add_argument('--no-revision-author', action='store_true',
                                         help='Author declined or withdrew that declaration; do not ask again')
        if name in ('snapshot', 'harvest'):
            action.add_argument('file', help='UTF-8 manuscript/passage file, or - for stdin')
            action.add_argument('--source', help='Stable passage identifier; default: project-relative path')
        if name == 'harvest':
            action.add_argument('--baseline', help='Compare to a specific snapshot instead of the latest one')
        if name == 'record':
            action.add_argument('--input', required=True, help='JSON update file, or - for stdin')
            action.add_argument('--profile-hash', help='Acknowledge an inspected and reconciled manually edited profile')
            action.add_argument('--author-request', action='store_true',
                                help='Explicit request to edit memory using author feedback, even when automatic learning is off')
        if name in ('show', 'forget', 'promote'):
            action.add_argument('id', nargs='?' if name == 'show' else None)
        if name == 'promote':
            action.add_argument('--author-revision', type=int, required=True,
                                help='Current revision of the linked author store')
        if name == 'restore':
            action.add_argument('version', type=int)
        if name in ('context', 'export'):
            for key in SCOPE_KEYS:
                action.add_argument('--' + key)
            action.add_argument('--budget', type=int, default=8000, help='Character budget for complete content records')
            action.add_argument('--examples', type=int, default=3, help='Maximum examples, 0..3')
        action.set_defaults(func=run)
