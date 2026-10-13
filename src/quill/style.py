"""Portable writing memory. Editorial inference belongs to the calling agent."""
from __future__ import annotations

from collections import Counter
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import tempfile
import time
import uuid

from .sync import find_repo_root

MODES = ('off', 'apply', 'learn')
STATUSES = ('tentative', 'observed', 'explicit', 'retired', 'needs-review')
ACTIVE = ('explicit', 'observed')
KINDS = ('feedback', 'revision', 'selection', 'observation')
ORIGINS = ('human', 'agent', 'mixed', 'unknown')
PURPOSES = ('style', 'exposition', 'scientific', 'evidence', 'venue', 'collaborator', 'unknown')
SCOPE_KEYS = ('section', 'audience', 'decision', 'genre', 'project')
TEXT_FIELDS = ('before', 'after', 'feedback', 'request', 'context')
CONTENT_FIELDS = ('before', 'after', 'feedback')
IDENTIFIER = re.compile(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}\Z')
HASH = re.compile(r'[a-f0-9]{64}\Z')
# Forgotten passages at least this long are also purged where they are embedded in other text.
EMBEDDED_MINIMUM = 40
STALE_LOCK_SECONDS = 600
PROFILE_WARNING = 40

PARAGRAPH_BREAK = re.compile(r'\r?\n[ \t]*(?:\r?\n[ \t]*)+')
BEGIN = re.compile(r'\\begin\{[^}]*\}')
END = re.compile(r'\\end\{[^}]*\}')
TOUCHES = {
    'math': re.compile(r'\$\$.*?\$\$|\$[^$]+\$|\\\[.*?\\\]|\\\(.*?\\\)'
                       r'|\\begin\{(equation|align|gather|multline|eqnarray)\*?\}.*?\\end\{\1\*?\}', re.S),
    'citation': re.compile(r'\\(?:no)?cite[a-zA-Z]*\*?(?:\[[^\]]*\])*\{[^}]*\}'),
    'reference': re.compile(r'\\(?:ref|eqref|cref|Cref|autoref|pageref|label)\{[^}]*\}'),
    'number': re.compile(r'(?<![A-Za-z\\])\d+(?:[.,]\d+)*%?'),
}


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def encoded(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode()


def identifier(value) -> str:
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise ValueError(f'invalid memory identifier: {value!r}')
    return value


def scope(value) -> dict:
    if not isinstance(value, dict) or set(value) - set(SCOPE_KEYS):
        raise ValueError(f'scope must use only {SCOPE_KEYS}')
    for values in value.values():
        if not isinstance(values, list) or not values or any(not isinstance(v, str) or not v.strip() for v in values):
            raise ValueError('scope values must be nonempty lists of strings')
    return value


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def default_store(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / '.quill/style/state.json').is_file():
            return candidate / '.quill/style'
    return find_repo_root(current) / '.quill/style'


def author_store(author: str) -> Path:
    identifier(author)
    return Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config')) / 'quill/authors' / author


def atomic_write(path: Path, data: bytes) -> None:
    if path.is_symlink():
        raise ValueError(f'refusing symlink: {path}')
    descriptor, temporary = tempfile.mkstemp(prefix='.write-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def installed_quill_skill(directory: Path) -> bool:
    skill = directory / 'SKILL.md'
    if not skill.is_file():
        return False
    try:
        head = skill.read_text(errors='replace')[:2000]
    except OSError:
        return False
    match = re.match(r'---\s*\n(.*?)\n---', head, re.S)
    return bool(match and re.search(r'^name:\s*["\']?quill["\']?\s*$', match.group(1), re.M))


def render_profile(data: dict) -> bytes:
    lines = ['# Quill writing profile', '',
             'Generated from state.json. Preserve manual edits and reconcile them before regenerating.', '']
    for pref in sorted(data['preferences'].values(), key=lambda p: p['id']):
        lines += [f"## {pref['id']} ({pref['status']})", '', pref['text'], '',
                  'Scope: ' + json.dumps(pref['scope'], ensure_ascii=False, sort_keys=True),
                  'Evidence: ' + ', '.join(pref['support']),
                  'Counterexamples: ' + ', '.join(pref['counter']), '']
    return ('\n'.join(lines) + '\n').encode()


def eligible(evidence: dict) -> bool:
    return (evidence['origin'] == 'human' and evidence['kind'] != 'observation'
            and evidence['purpose'] in ('style', 'exposition'))


def supported(pref: dict, evidence: dict) -> bool:
    usable = [evidence[i] for i in pref['support'] if i in evidence and eligible(evidence[i])]
    if pref['status'] in ACTIVE and len({e['author'] for e in usable}) > 1:
        return False
    if pref['status'] == 'explicit':
        return any(e['kind'] == 'feedback' for e in usable)
    if pref['status'] == 'observed':
        return (len({e['lineage'] for e in usable}) >= 2
                and len({e['content_hash'] for e in usable}) >= 2)
    return True


def check_preference(pref) -> dict:
    if not isinstance(pref, dict) or set(pref) - {'id', 'text', 'scope', 'status', 'support', 'counter'}:
        raise ValueError('preferences accept only id, text, scope, status, support, and counter')
    identifier(pref.get('id'))
    if not isinstance(pref.get('text'), str) or not pref['text'].strip():
        raise ValueError(f"preference {pref['id']} requires text")
    if pref.get('status', 'tentative') not in STATUSES:
        raise ValueError(f'preference status must be one of {STATUSES}')
    scope(pref.get('scope', {}))
    for field in ('support', 'counter'):
        values = pref.get(field, [])
        if not isinstance(values, list) or any(not isinstance(i, str) for i in values):
            raise ValueError(f'preference {field} must be a list of evidence IDs')
    return pref


def check_evidence(entry) -> dict:
    allowed = {'id', 'kind', 'origin', 'author', 'purpose', 'scope', 'lineage', 'source',
               'baseline', *TEXT_FIELDS}
    if not isinstance(entry, dict) or set(entry) - allowed:
        extra = sorted(set(entry) - allowed) if isinstance(entry, dict) else []
        raise ValueError(f'unsupported evidence fields: {extra}')
    if entry.get('kind') not in KINDS:
        raise ValueError(f'evidence kind must be one of {KINDS}')
    if entry.get('origin', 'unknown') not in ORIGINS:
        raise ValueError(f'evidence origin must be one of {ORIGINS}')
    if entry.get('purpose', 'unknown') not in PURPOSES:
        raise ValueError(f'evidence purpose must be one of {PURPOSES}')
    if entry.get('author') is not None and not isinstance(entry['author'], str):
        raise ValueError('author attribution must be a string or null')
    for field in ('source', 'lineage'):
        if field in entry and not isinstance(entry[field], str):
            raise ValueError(f'evidence {field} must be a string')
    if entry.get('baseline') is not None and not isinstance(entry['baseline'], str):
        raise ValueError('evidence baseline must be a snapshot ID or null')
    scope(entry.get('scope', {}))
    return entry


def paragraph_spans(text: str) -> list[list[int]]:
    """Exact paragraph spans; blank lines inside a LaTeX environment do not split it."""
    spans, position = [], 0
    for match in PARAGRAPH_BREAK.finditer(text):
        if text[position:match.start()].strip():
            spans.append([position, match.start()])
        position = match.end()
    if text[position:].strip():
        spans.append([position, len(text)])
    merged, depth = [], 0
    for start, end in spans:
        if depth > 0 and merged:
            merged[-1][1] = end
        else:
            merged.append([start, end])
        chunk = text[start:end]
        depth = max(0, depth + len(BEGIN.findall(chunk)) - len(END.findall(chunk)))
    return merged


def touches(before: str, after: str) -> list[str]:
    return [name for name, pattern in TOUCHES.items()
            if Counter(m.group(0) for m in pattern.finditer(before))
            != Counter(m.group(0) for m in pattern.finditer(after))]


def similar(left: str, right: str) -> bool:
    matcher = difflib.SequenceMatcher(None, left, right, autojunk=False)
    return matcher.quick_ratio() >= 0.9 and matcher.ratio() >= 0.9


def align_block(old: list[str], new: list[str], i1: int, i2: int, j1: int, j2: int) -> list[tuple]:
    """Pair edited paragraphs separately; keep a split or merged paragraph with its source."""
    if i2 - i1 == j2 - j1:
        return [(i1 + k, i1 + k + 1, j1 + k, j1 + k + 1) for k in range(i2 - i1)]
    def score(p, q):
        left = '\n\n'.join(s.strip() for s in old[i:i + p])
        right = '\n\n'.join(s.strip() for s in new[j:j + q])
        return difflib.SequenceMatcher(None, left, right, autojunk=False).ratio()
    groups, i, j = [], i1, j1
    while i < i2 and j < j2:
        shapes = [(p, q) for p, q in ((1, 1), (1, 2), (1, 3), (2, 1), (3, 1)) if i + p <= i2 and j + q <= j2]
        best, (p, q) = max((score(p, q), (p, q)) for p, q in shapes)
        if best < 0.5:
            p, q = 1, 1
        groups.append((i, i + p, j, j + q))
        i, j = i + p, j + q
    if i < i2 or j < j2:
        groups.append((i, i2, j, j2))
    return groups


class StyleStore:
    def __init__(self, path: Path):
        path = Path(path).expanduser().absolute()
        # Resolve platform aliases such as /tmp, but never follow a store symlink.
        if path.is_symlink():
            raise ValueError('memory store must not be a symlink')
        self.path = path.resolve()
        for parent in (self.path, *self.path.parents):
            if installed_quill_skill(parent):
                raise ValueError('personal memory must be outside installed skill folders')

    def file(self, relative: str) -> Path:
        path = self.path / relative
        for parent in (path, *path.parents):
            if parent == self.path.parent:
                break
            if parent.is_symlink():
                raise ValueError(f'refusing memory symlink: {parent}')
        return path

    def stale_lock(self, lock: Path) -> bool:
        try:
            owner = json.loads(lock.read_bytes())
            pid, host = int(owner['pid']), owner['host']
        except (OSError, ValueError, KeyError, TypeError):
            try:
                return time.time() - lock.stat().st_mtime > STALE_LOCK_SECONDS
            except OSError:
                return True
        # os.kill terminates processes on Windows, and a remote host's PIDs are not ours to check.
        if os.name == 'nt' or host != socket.gethostname():
            return False
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return True
        except PermissionError:
            return False
        return False

    @contextmanager
    def locked(self):
        lock = self.file('.lock')
        token = uuid.uuid4().hex
        content = encoded({'pid': os.getpid(), 'host': socket.gethostname(), 'time': now(), 'token': token})
        for attempt in (1, 2):
            try:
                descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                break
            except FileExistsError as exc:
                if attempt == 1 and self.stale_lock(lock):
                    lock.unlink(missing_ok=True)
                    continue
                raise ValueError('memory is busy; retry after the other writer finishes') from exc
        try:
            with os.fdopen(descriptor, 'wb') as stream:
                stream.write(content)
            yield
        finally:
            try:
                if lock.read_bytes() == content:
                    lock.unlink()
            except OSError:
                pass

    def load(self) -> dict:
        state = json.loads(self.file('state.json').read_bytes())
        if (not isinstance(state, dict) or state.get('schema_version') != 1 or type(state.get('revision')) is not int
                or state['revision'] < 0):
            raise ValueError('unsupported or malformed memory state')
        state.setdefault('forgotten_ids', [])
        state.setdefault('forgotten_hashes', [])
        state.pop('history', None)
        self.validate_data(state['data'])
        for value in state['forgotten_ids']:
            identifier(value)
        if any(not isinstance(h, str) or not HASH.fullmatch(h) for h in state['forgotten_hashes']):
            raise ValueError('invalid forgotten content hash')
        return state

    @staticmethod
    def validate_data(data: dict) -> None:
        if not isinstance(data, dict):
            raise ValueError('malformed memory data')
        data.setdefault('revision_author', None)
        data.setdefault('revision_author_asked', False)
        if data.get('mode') not in MODES:
            raise ValueError('invalid memory mode')
        if data.get('author_store') is not None and not isinstance(data['author_store'], str):
            raise ValueError('invalid author store path')
        if data['revision_author'] is not None:
            identifier(data['revision_author'])
        if not isinstance(data['revision_author_asked'], bool):
            raise ValueError('revision_author_asked must be true or false')
        for name in ('evidence', 'preferences', 'snapshots'):
            if not isinstance(data.get(name), dict):
                raise ValueError(f'invalid {name}')
            for key, record in data[name].items():
                if not isinstance(record, dict) or identifier(key) != record.get('id'):
                    raise ValueError(f'record identifier mismatch: {key}')
        for record in data['evidence'].values():
            check_evidence({k: v for k, v in record.items()
                            if k not in ('id', 'blobs', 'content_hash', 'fingerprint', 'time')})
            if record['origin'] == 'human' and not (record.get('author') or '').strip():
                raise ValueError('human evidence requires explicit author attribution')
            if not isinstance(record.get('blobs'), dict) or not isinstance(record.get('lineage'), str):
                raise ValueError(f"malformed evidence record: {record['id']}")
            for blob in record['blobs'].values():
                if not isinstance(blob, str) or not HASH.fullmatch(blob):
                    raise ValueError('invalid evidence content reference')
        for record in data['snapshots'].values():
            if not isinstance(record.get('blob'), str) or not HASH.fullmatch(record['blob']):
                raise ValueError('invalid snapshot content reference')
        for pref in data['preferences'].values():
            check_preference(pref)
            for field in ('support', 'counter'):
                if field not in pref or any(i not in data['evidence'] for i in pref[field]):
                    raise ValueError(f"preference {pref['id']} references missing evidence")
            if not supported(pref, data['evidence']):
                raise ValueError(f"active preference {pref['id']} lacks appropriate independent human evidence")

    def blob(self, key: str) -> bytes:
        if not HASH.fullmatch(key):
            raise ValueError('invalid content hash')
        value = self.file(f'text/{key}.txt').read_bytes()
        if digest(value) != key:
            raise ValueError('stored content hash mismatch')
        return value

    def edited_profile(self, state: dict) -> bool:
        profile = self.file('profile.md')
        return profile.exists() and profile.read_bytes() != render_profile(state['data'])

    def read_history(self) -> list:
        path = self.file('history.jsonl')
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]

    @staticmethod
    def history_bytes(entries: list) -> bytes:
        return ''.join(json.dumps(e, ensure_ascii=False, sort_keys=True) + '\n' for e in entries).encode()

    def init(self, mode: str = 'off', linked_author: Path | None = None) -> dict:
        if mode not in MODES:
            raise ValueError('invalid memory mode')
        if self.path.exists() and any(self.path.iterdir()):
            raise ValueError('store already exists or is nonempty; inspect and use configure')
        link = self.check_link(linked_author) if linked_author else None
        self.path.mkdir(parents=True, exist_ok=True)
        with self.locked():
            if self.file('state.json').exists():
                raise ValueError('store was initialized by another writer')
            self.file('text').mkdir()
            state = {'schema_version': 1, 'revision': 0, 'forgotten_ids': [], 'forgotten_hashes': [],
                     'data': {'mode': mode, 'author_store': link, 'revision_author': None,
                              'revision_author_asked': False,
                              'evidence': {}, 'preferences': {}, 'snapshots': {}}}
            atomic_write(self.file('.gitignore'), b'*\n')
            atomic_write(self.file('state.json'), encoded(state))
            atomic_write(self.file('profile.md'), render_profile(state['data']))
        return self.summary(state)

    def check_link(self, path: Path) -> str:
        author = StyleStore(path)
        if author.path == self.path or author.load()['data'].get('author_store'):
            raise ValueError('author links must point to a different, unlinked store')
        return str(author.path)

    def summary(self, state: dict) -> dict:
        data = state['data']
        active = sum(p['status'] in ACTIVE for p in data['preferences'].values())
        return {'store': str(self.path), 'revision': state['revision'], 'mode': data['mode'],
                'author_store': data['author_store'], 'revision_author': data.get('revision_author'),
                'active_preferences': active, 'profile_edited': self.edited_profile(state)}

    def commit(self, old: dict, data: dict, blobs: dict | None = None,
               profile_hash: str | None = None, history: list | None = None,
               forgotten_ids: list | None = None, forgotten_hashes: list | None = None) -> dict:
        self.validate_data(data)
        profile = self.file('profile.md')
        profile_before = profile.read_bytes() if profile.exists() else None
        edited = profile_before is not None and profile_before != render_profile(old['data'])
        if profile_hash is not None and (profile_before is None or digest(profile_before) != profile_hash):
            raise ValueError('profile changed since it was inspected')
        state = deepcopy(old)
        state['revision'] += 1
        state['data'] = data
        if forgotten_ids is not None:
            state['forgotten_ids'] = forgotten_ids
        if forgotten_hashes is not None:
            state['forgotten_hashes'] = forgotten_hashes
        # History holds profile versions only; evidence and snapshots are append-only until forgotten.
        tracked = ('preferences', 'mode', 'author_store')
        if history is None and any(old['data'].get(k) != data.get(k) for k in tracked):
            history = self.read_history() + [{'revision': old['revision'], 'time': now(),
                                              **{k: old['data'].get(k) for k in tracked}}]
        history_file = self.file('history.jsonl')
        history_before = history_file.read_bytes() if history_file.exists() else None
        created = []
        try:
            for key, value in (blobs or {}).items():
                if key in state['forgotten_hashes']:
                    raise ValueError('content was forgotten; refusing to reintroduce it')
                path = self.file(f'text/{key}.txt')
                if path.exists() and path.read_bytes() != value:
                    raise ValueError('stored content hash mismatch')
                if not path.exists():
                    atomic_write(path, value)
                    created.append(path)
            if history is not None:
                atomic_write(history_file, self.history_bytes(history))
            atomic_write(self.file('state.json'), encoded(state))
        except (OSError, ValueError):
            for path in created:
                path.unlink(missing_ok=True)
            if history is not None:
                if history_before is None:
                    history_file.unlink(missing_ok=True)
                elif history_file.read_bytes() != history_before:
                    atomic_write(history_file, history_before)
            raise
        if not edited or profile_hash is not None:
            profile_current = profile.read_bytes() if profile.exists() else None
            if profile_current == profile_before:
                atomic_write(profile, render_profile(data))
        return state

    def checked(self, revision: int, learn: bool = False) -> dict:
        state = self.load()
        if type(revision) is not int or state['revision'] != revision:
            raise ValueError(f"stale memory revision; current revision is {state['revision']}")
        if learn and state['data']['mode'] != 'learn':
            raise ValueError('learning is disabled; writing can continue without recording memory')
        return state

    def configure(self, revision: int, mode: str | None = None,
                  linked_author: Path | None = None, unlink: bool = False,
                  revision_author: str | None = None, decline_revision_author: bool = False) -> dict:
        if revision_author is not None and decline_revision_author:
            raise ValueError('choose either a revision author or none')
        with self.locked():
            state = self.checked(revision)
            data = deepcopy(state['data'])
            if mode is not None:
                data['mode'] = mode
            if linked_author is not None:
                data['author_store'] = self.check_link(linked_author)
            if unlink:
                data['author_store'] = None
            if revision_author is not None:
                data['revision_author'] = identifier(revision_author)
                data['revision_author_asked'] = True
            if decline_revision_author:
                data['revision_author'] = None
                data['revision_author_asked'] = True
            return self.summary(self.commit(state, data))

    def snapshot(self, revision: int, source: str, content: bytes) -> dict:
        content.decode('utf-8')
        if not source.strip():
            raise ValueError('snapshot requires a stable source identifier')
        with self.locked():
            state = self.checked(revision, learn=True)
            data = deepcopy(state['data'])
            # JSON key order is not lineage order: select using the committed sequence.
            matches = [s for s in data['snapshots'].values() if s['source'] == source]
            previous = max(matches, key=lambda s: s['sequence']) if matches else None
            key = digest(content)
            if previous and previous['blob'] == key:
                return {**self.summary(state), 'snapshot': previous, 'duplicate': True}
            entry = {'id': 's-' + uuid.uuid4().hex, 'source': source, 'blob': key,
                     'origin': 'agent', 'parent': previous['id'] if previous else None,
                     'sequence': state['revision'] + 1, 'time': now()}
            data['snapshots'][entry['id']] = entry
            result = self.commit(state, data, {key: content})
            return {**self.summary(result), 'snapshot': entry, 'duplicate': False}

    def harvest(self, source: str, content: bytes, baseline: str | None = None) -> dict:
        after = content.decode('utf-8')
        state = self.load()
        data = state['data']
        summary = self.summary(state)
        if data['mode'] != 'learn':
            return {**summary, 'candidates': [], 'reason': 'learning disabled'}
        matches = [s for s in data['snapshots'].values() if s['source'] == source]
        previous = (data['snapshots'].get(baseline) if baseline else
                    max(matches, key=lambda s: s['sequence']) if matches else None)
        if not previous or previous['source'] != source:
            return {**summary, 'candidates': [], 'reason': 'no matching baseline'}
        before = self.blob(previous['blob']).decode('utf-8')
        if before == after:
            return {**summary, 'candidates': [], 'reason': 'unchanged'}
        author = data['revision_author']
        attribution = ({'kind': 'revision', 'origin': 'human', 'author': author} if author else
                       {'kind': 'observation', 'origin': 'unknown', 'author': None})
        old_spans, new_spans = paragraph_spans(before), paragraph_spans(after)
        old = [before[s:e] for s, e in old_spans]
        new = [after[s:e] for s, e in new_spans]
        matcher = difflib.SequenceMatcher(None, [p.strip() for p in old], [p.strip() for p in new],
                                          autojunk=False)
        changes = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'replace':
                changes += align_block(old, new, i1, i2, j1, j2)
            elif tag != 'equal':
                changes.append((i1, i2, j1, j2))
        blocks = []
        for i1, i2, j1, j2 in changes:
            removed = before[old_spans[i1][0]:old_spans[i2 - 1][1]] if i2 > i1 else ''
            added = after[new_spans[j1][0]:new_spans[j2 - 1][1]] if j2 > j1 else ''
            neighbours = [old[i1 - 1] if i1 > 0 else '', old[i2] if i2 < len(old) else '']
            blocks.append({'removed': old[i1:i2], 'added': new[j1:j2], 'before': removed, 'after': added,
                           'context': '\n\n[changed passage]\n\n'.join(neighbours).strip()})
        candidates = []
        for index, block in enumerate(blocks):
            others = [b for i, b in enumerate(blocks) if i != index]
            moved = any(similar(p.strip(), q.strip()) for p in block['removed']
                        for other in others for q in other['added']) or any(
                similar(p.strip(), q.strip()) for p in block['added']
                for other in others for q in other['removed'])
            anchor = block['before'] or block['after']
            record = {**attribution, 'purpose': 'unknown', 'scope': {}, 'source': source,
                      'baseline': previous['id'], 'lineage': f"{source}#{digest(anchor.encode())[:16]}",
                      'before': block['before'], 'after': block['after']}
            if block['context']:
                record['context'] = block['context']
            candidates.append({'record': record, 'touches': touches(block['before'], block['after']),
                               'moved': moved})
        return {**summary, 'candidates': candidates,
                'attribution': 'declared' if author else 'unknown',
                'attribution_needed': not author and not data['revision_author_asked'],
                'diff': ''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                                                   fromfile='agent baseline', tofile='current text'))}

    def normalize_evidence(self, item: dict, blobs: dict) -> tuple[str | None, dict]:
        entry = deepcopy(check_evidence(item))
        supplied_id = entry.pop('id', None)
        contents = {}
        for field in TEXT_FIELDS:
            if field in entry:
                value = entry.pop(field)
                if not isinstance(value, str):
                    raise ValueError('evidence text must be a string')
                raw = value.encode()
                contents[field] = digest(raw)
                blobs[digest(raw)] = raw
        if not any(blobs[contents[f]].strip() for f in CONTENT_FIELDS if f in contents):
            raise ValueError('evidence requires nonempty before/after or feedback text')
        kind = entry['kind']
        if kind == 'feedback' and 'feedback' not in contents:
            raise ValueError('feedback evidence requires feedback text')
        if kind in ('revision', 'observation', 'selection') and not {'before', 'after'} <= contents.keys():
            raise ValueError('revision, selection, and observation require before and after text')
        entry.setdefault('scope', {})
        entry.setdefault('origin', 'unknown')
        entry.setdefault('author', None)
        entry.setdefault('purpose', 'unknown')
        entry.setdefault('source', '')
        entry.setdefault('baseline', None)
        if entry['origin'] == 'human' and not (entry['author'] or '').strip():
            raise ValueError('human evidence requires explicit author attribution')
        entry['blobs'] = contents
        entry['content_hash'] = digest(encoded({k: v for k, v in contents.items() if k in CONTENT_FIELDS}))
        if 'lineage' not in entry:
            # Distinct passages in one file are independent; the same passage shares a lineage.
            anchor = next((contents[f] for f in ('before', 'feedback', 'after')
                           if f in contents and blobs[contents[f]].strip()), entry['content_hash'])
            entry['lineage'] = f"{entry['source']}#{anchor[:16]}" if entry['source'] else entry['content_hash']
        if not entry['lineage']:
            raise ValueError('evidence requires a nonempty lineage')
        entry['fingerprint'] = digest(encoded(entry))
        return supplied_id, entry

    def record(self, revision: int, payload: dict, profile_hash: str | None = None,
               author_request: bool = False) -> dict:
        if not isinstance(payload, dict) or set(payload) - {'evidence', 'preferences'}:
            raise ValueError('record accepts evidence and preferences lists')
        if any(not isinstance(value, list) for value in payload.values()):
            raise ValueError('record accepts evidence and preferences lists')
        if author_request and (not payload.get('evidence') or any(
                not isinstance(e, dict) or e.get('kind') != 'feedback' or e.get('origin') != 'human'
                or e.get('purpose') not in ('style', 'exposition') for e in payload['evidence'])):
            raise ValueError('an explicit memory-management request requires attributed author feedback')
        for pref in payload.get('preferences', []):
            check_preference(pref)
        with self.locked():
            state = self.checked(revision, learn=not author_request)
            data = deepcopy(state['data'])
            blobs, aliases = {}, {}
            for item in payload.get('evidence', []):
                supplied_id, entry = self.normalize_evidence(item, blobs)
                fingerprint = entry['fingerprint']
                duplicate = next((e for e in data['evidence'].values() if e['fingerprint'] == fingerprint), None)
                key = identifier(supplied_id or 'e-' + fingerprint[:24])
                if key in state['forgotten_ids'] or entry['content_hash'] in state['forgotten_hashes']:
                    raise ValueError('evidence was forgotten')
                if duplicate:
                    aliases[key] = duplicate['id']
                    continue
                if key in data['evidence']:
                    raise ValueError('evidence is immutable; use a new identifier')
                entry.update(id=key, time=now())
                data['evidence'][key] = entry
            for item in payload.get('preferences', []):
                pref = deepcopy(item)
                key = pref['id']
                if key in state['forgotten_ids']:
                    raise ValueError('preference was forgotten')
                pref.setdefault('scope', {})
                pref.setdefault('status', 'tentative')
                for field in ('support', 'counter'):
                    pref[field] = list(dict.fromkeys(aliases.get(i, i) for i in pref.get(field, [])))
                self.check_explicit_change(data, data['preferences'].get(key), pref)
                data['preferences'][key] = pref
            if data == state['data'] and profile_hash is None:
                return {**self.summary(state), 'aliases': aliases, 'duplicate': True}
            result = self.commit(state, data, blobs, profile_hash=profile_hash)
            return {**self.summary(result), 'aliases': aliases, 'duplicate': False}

    @staticmethod
    def check_explicit_change(data: dict, previous: dict | None, pref: dict) -> None:
        if previous and previous['status'] == 'explicit' and any(
                pref[field] != previous[field] for field in ('text', 'scope', 'status')):
            added = set(pref['support']) - set(previous['support'])
            if not any(i in data['evidence'] and eligible(data['evidence'][i])
                       and data['evidence'][i]['kind'] == 'feedback' for i in added):
                raise ValueError('changing an explicit preference requires new explicit author feedback')

    def show(self, key: str | None = None) -> dict:
        state = self.load()
        summary = self.summary(state)
        if summary['active_preferences'] > PROFILE_WARNING:
            summary['warnings'] = [consolidation_warning(self.path, summary['active_preferences'])]
        if key is None:
            return {**summary, 'data': state['data']}
        for name in ('evidence', 'preferences', 'snapshots'):
            if key in state['data'][name]:
                entry = deepcopy(state['data'][name][key])
                for field, blob in entry.get('blobs', {}).items():
                    entry[field] = self.blob(blob).decode('utf-8')
                if 'blob' in entry:
                    entry['content'] = self.blob(entry['blob']).decode('utf-8')
                return {**summary, 'record': entry}
        raise ValueError('memory record not found')

    def history(self) -> list:
        return [{'revision': h['revision'], 'time': h['time']} for h in self.read_history()]

    def restore(self, revision: int, version: int) -> dict:
        """Restore a profile version. Evidence, mode, and author scope stay current."""
        with self.locked():
            state = self.checked(revision)
            if type(version) is not int or not 0 <= version < state['revision']:
                raise ValueError('history version not found')
            # An entry records the profile that held until that revision; later writes left it unchanged.
            match = min((h for h in self.read_history() if h['revision'] >= version),
                        key=lambda h: h['revision'], default=None)
            data = deepcopy(state['data'])
            data['preferences'] = {}
            for key, pref in (match or state['data'])['preferences'].items():
                pref = deepcopy(pref)
                for field in ('support', 'counter'):
                    pref[field] = [i for i in pref[field] if i in data['evidence']]
                if not supported(pref, data['evidence']):
                    pref['status'] = 'needs-review'
                data['preferences'][key] = pref
            return self.summary(self.commit(state, data))

    def forget(self, revision: int, key: str) -> dict:
        with self.locked():
            state = self.checked(revision)
            if self.edited_profile(state):
                raise ValueError('reconcile the edited profile before forgetting; opaque manual text may contain the material')
            current = state['data']
            history = self.read_history()
            in_history = any(key in h['preferences'] for h in history)
            if key not in state['forgotten_ids'] and not in_history and not any(
                    key in current[n] for n in ('evidence', 'preferences', 'snapshots')):
                raise ValueError('memory record not found')
            removed = {key}
            # A forgotten preference takes evidence that no other current preference uses.
            target = current['preferences'].get(key) or next(
                (h['preferences'][key] for h in reversed(history) if key in h['preferences']), None)
            if target:
                shared = {i for k, p in current['preferences'].items() if k != key
                          for i in p['support'] + p['counter']}
                removed.update(i for i in target['support'] + target['counter'] if i not in shared)

            def refs(item: dict, name: str) -> dict:
                return item.get('blobs', {}) if name == 'evidence' else {'content': item['blob']}

            content = CONTENT_FIELDS + ('content',)
            hashes = set(state['forgotten_hashes'])
            passages = set()       # exact passage blobs; records sharing one are the same material
            incidental = set()     # request/context blobs; purged only when nothing else uses them
            needles = set()        # long passages also purged where embedded elsewhere
            quoted = {}            # evidence ID -> its content, for scrubbing rules derived from it
            for name in ('evidence', 'snapshots'):
                for item in current[name].values():
                    if item['id'] not in removed:
                        continue
                    for field, ref in refs(item, name).items():
                        value = self.blob(ref).decode('utf-8').strip()
                        if field not in content:
                            incidental.add(ref)
                        elif value:
                            passages.add(ref)
                            quoted.setdefault(item['id'], set()).add(value)
                            if len(value) >= EMBEDDED_MINIMUM:
                                needles.add(value)
                    if name == 'evidence':
                        hashes.add(item['content_hash'])
            changed = True
            while changed:
                changed = False
                for name in ('evidence', 'snapshots'):
                    for item in current[name].values():
                        if item['id'] in removed:
                            continue
                        for field, ref in refs(item, name).items():
                            if field in content and (ref in passages or needles and any(
                                    n in self.blob(ref).decode('utf-8') for n in needles)):
                                passages.add(ref)
                                removed.add(item['id'])
                                changed = True
                                break
            survivors = {ref for name in ('evidence', 'snapshots') for item in current[name].values()
                         if item['id'] not in removed for ref in refs(item, name).values()}
            hashes |= passages | (incidental - survivors)
            evidence = {i: e for i, e in current['evidence'].items() if i not in removed}

            def scrub(preferences: dict) -> dict:
                result = {}
                for pid, pref in preferences.items():
                    if pid in removed:
                        continue
                    pref = deepcopy(pref)
                    lost = [i for i in pref['support'] + pref['counter'] if i in removed]
                    for field in ('support', 'counter'):
                        pref[field] = [i for i in pref[field] if i in evidence]
                    exposed = set(needles)
                    for i in lost:
                        exposed |= quoted.get(i, set())
                    if any(text in pref['text'] for text in exposed):
                        pref['text'] = 'Preference needs review after supporting material was forgotten.'
                        pref['status'] = 'needs-review'
                    if not supported(pref, evidence):
                        pref['status'] = 'needs-review'
                    result[pid] = pref
                return result

            data = deepcopy(current)
            data['evidence'] = evidence
            data['snapshots'] = {i: s for i, s in current['snapshots'].items() if i not in removed}
            data['preferences'] = scrub(current['preferences'])
            for item in data['evidence'].values():
                if item.get('baseline') in removed:
                    item['baseline'] = None
            for item in data['snapshots'].values():
                if item['parent'] in removed:
                    item['parent'] = None
            history = [{**h, 'preferences': scrub(h['preferences'])} for h in history]
            history.append({'revision': state['revision'], 'time': now(), 'mode': current['mode'],
                            'author_store': current['author_store'], 'preferences': data['preferences']})
            result = self.commit(state, data, history=history,
                                 forgotten_ids=sorted(set(state['forgotten_ids']) | removed),
                                 forgotten_hashes=sorted(hashes))
            # Metadata no longer references these payloads. Also clean any orphaned pre-commit writes.
            used = {s['blob'] for s in result['data']['snapshots'].values()}
            used.update(b for e in result['data']['evidence'].values() for b in e['blobs'].values())
            for path in self.file('text').glob('*.txt'):
                if path.stem not in used:
                    self.file(f'text/{path.name}').unlink()
            return {**self.summary(result), 'forgotten': sorted(removed)}

    def promote(self, revision: int, key: str, author_revision: int) -> dict:
        """Copy a project preference and its evidence into the linked author store."""
        state = self.checked(revision)
        if not state['data']['author_store']:
            raise ValueError('link an author store before promoting a preference')
        pref = state['data']['preferences'].get(key)
        if pref is None:
            raise ValueError('preference not found')
        author = StyleStore(Path(state['data']['author_store']))
        with author.locked():
            target = author.checked(author_revision)
            data = deepcopy(target['data'])
            if key in target['forgotten_ids']:
                raise ValueError('preference was forgotten in the author store')
            blobs, aliases = {}, {}
            for eid in dict.fromkeys(pref['support'] + pref['counter']):
                entry = deepcopy(state['data']['evidence'][eid])
                if eid in target['forgotten_ids'] or entry['content_hash'] in target['forgotten_hashes']:
                    raise ValueError(f'evidence {eid} was forgotten in the author store')
                duplicate = next((e for e in data['evidence'].values()
                                  if e['fingerprint'] == entry['fingerprint']), None)
                if duplicate:
                    aliases[eid] = duplicate['id']
                    continue
                if eid in data['evidence']:
                    raise ValueError(f'author store already has different evidence named {eid}')
                for ref in entry['blobs'].values():
                    blobs[ref] = self.blob(ref)
                # Snapshots are project-local; keep the passage but not a dangling baseline.
                entry['baseline'] = None
                data['evidence'][eid] = entry
            copy = deepcopy(pref)
            for field in ('support', 'counter'):
                copy[field] = list(dict.fromkeys(aliases.get(i, i) for i in copy[field]))
            existing = data['preferences'].get(key)
            if existing == copy:
                return {**author.summary(target), 'promoted': key, 'duplicate': True}
            if existing is not None:
                raise ValueError('author store already has a different preference with this ID; correct it there')
            data['preferences'][key] = copy
            result = author.commit(target, data, blobs)
            return {**author.summary(result), 'promoted': key, 'aliases': aliases, 'duplicate': False}


def consolidation_warning(path: Path, count: int) -> str:
    return (f'{count} active preferences in {path}; consolidate overlapping rules or retire '
            f'stale ones so the profile stays short.')


def writing_context(store: StyleStore, query: dict | None = None, budget: int = 8000,
                    examples: int = 3) -> dict:
    """Bound complete records, never truncate a preference's qualifying conditions."""
    if budget < 256 or not 0 <= examples <= 3:
        raise ValueError('context budget must be >=256 characters and examples must be 0..3')
    query = query or {}
    if set(query) - set(SCOPE_KEYS):
        raise ValueError('unknown context scope')
    state = store.load()
    result = {**store.summary(state), 'preferences': [], 'examples': [], 'warnings': [], 'scope_options': {}}
    if state['data']['mode'] == 'off':
        return result
    stores = [(store, state)]
    if state['data']['author_store']:
        try:
            author = StyleStore(Path(state['data']['author_store']))
            author_state = author.load()
            if author_state['data']['mode'] != 'off':
                stores.append((author, author_state))
        except (OSError, ValueError, KeyError, TypeError) as exc:
            result['warnings'].append(f'Author memory unavailable: {exc}')
    remaining = budget
    choices = []
    options = {key: set() for key in SCOPE_KEYS}
    for current, current_state in stores:
        active = [p for p in current_state['data']['preferences'].values() if p['status'] in ACTIVE]
        if len(active) > PROFILE_WARNING:
            result['warnings'].append(consolidation_warning(current.path, len(active)))
        for pref in active:
            for key, values in pref['scope'].items():
                options[key].update(values)
        if current.edited_profile(current_state):
            manual = current.file('profile.md').read_text()
            result['warnings'].append(f'Manually edited profile needs reconciliation: {current.path}')
            if len(manual) <= remaining:
                result.setdefault('manual_profiles', []).append({'store': str(current.path), 'text': manual})
                remaining -= len(manual)
            else:
                result['warnings'].append('Edited profile exceeds context budget; read it before applying conflicting memory.')
            # Never apply stale generated records alongside an unreconciled manual profile.
            continue
        candidates = [p for p in active if all(query.get(k) in values for k, values in p['scope'].items())]
        candidates.sort(key=lambda p: (p['status'] != 'explicit', -len(p['scope']), p['id']))
        evidence = current_state['data']['evidence']
        for pref in candidates:
            entry = {'store': str(current.path), **pref}
            size = len(encoded(entry).decode())
            if size > remaining:
                result['warnings'].append(f"Preference omitted by budget: {pref['id']}")
                continue
            result['preferences'].append(entry)
            remaining -= size
            # Counterexamples first, then support; newest evidence first within each.
            for ids in (pref['counter'], pref['support']):
                for key in sorted(ids, key=lambda i: evidence[i].get('time', ''), reverse=True):
                    choices.append((current, key))
    seen = set()
    for current, key in choices:
        if len(result['examples']) >= examples:
            break
        if (current.path, key) in seen:
            continue
        seen.add((current.path, key))
        try:
            entry = {'store': str(current.path), **current.show(key)['record']}
        except (OSError, ValueError) as exc:
            result['warnings'].append(f'Example {key} unavailable: {exc}')
            continue
        if not all(query.get(k) in values for k, values in entry['scope'].items()):
            continue
        size = len(encoded(entry).decode())
        if size <= remaining:
            result['examples'].append(entry)
            remaining -= size
    result['content_characters'] = budget - remaining
    result['scope_options'] = {key: sorted(values)[:20] for key, values in options.items() if values}
    if any(values and query.get(key) not in values for key, values in options.items()):
        result['warnings'].append('Some scope tags are missing or unmatched. Use scope_options to select semantically appropriate tags; do not broaden a rule to force a match.')
    return result


def export_context(context: dict) -> str:
    lines = ['# Portable Quill writing memory', '',
             'Use only for the stated scopes. Examples illustrate writing decisions, not research evidence.', '']
    for pref in context['preferences']:
        lines += [f"## {pref['id']}", '', pref['text'], '',
                  'Scope: ' + json.dumps(pref['scope'], ensure_ascii=False), '']
    for profile in context.get('manual_profiles', []):
        lines += ['## Author-edited profile (reconcile before updating)', '', profile['text'], '']
    for entry in context['examples']:
        lines += [f"## Example {entry['id']}", '',
                  f"Kind: {entry['kind']}; origin: {entry['origin']}; purpose: {entry['purpose']}", '']
        for field in ('before', 'after', 'feedback'):
            if field in entry:
                lines += [field.capitalize() + ':', '', entry[field], '']
    for warning in context['warnings']:
        lines += ['Note: ' + warning, '']
    return '\n'.join(lines) + '\n'
