"""Portable writing memory. Editorial inference belongs to the calling agent."""
from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import uuid

from .sync import find_repo_root

MODES = ('off', 'apply', 'learn')
STATUSES = ('tentative', 'observed', 'explicit', 'retired', 'needs-review')
KINDS = ('feedback', 'revision', 'selection', 'observation')
PURPOSES = ('style', 'exposition', 'scientific', 'evidence', 'venue', 'collaborator', 'unknown')
SCOPE_KEYS = ('section', 'audience', 'decision', 'genre', 'project')
IDENTIFIER = re.compile(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}\Z')
HASH = re.compile(r'[a-f0-9]{64}\Z')


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def encoded(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode()


def identifier(value) -> str:
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise ValueError('invalid memory identifier')
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
    return find_repo_root(start) / '.quill/style'


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
    if pref['status'] in ('explicit', 'observed') and len({e['author'] for e in usable}) > 1:
        return False
    if pref['status'] == 'explicit':
        return any(e['kind'] == 'feedback' for e in usable)
    if pref['status'] == 'observed':
        return (len({e['lineage'] for e in usable}) >= 2
                and len({e['content_hash'] for e in usable}) >= 2)
    return True


class StyleStore:
    def __init__(self, path: Path):
        path = Path(path).expanduser().absolute()
        # Resolve platform aliases such as /tmp, but never follow a store symlink.
        if path.is_symlink():
            raise ValueError('memory store must not be a symlink')
        self.path = path.resolve()
        for parent in (self.path, *self.path.parents):
            if (parent / 'SKILL.md').is_file():
                raise ValueError('personal memory must be outside installed skill folders')

    def file(self, relative: str) -> Path:
        path = self.path / relative
        for parent in (path, *path.parents):
            if parent == self.path.parent:
                break
            if parent.is_symlink():
                raise ValueError(f'refusing memory symlink: {parent}')
        return path

    @contextmanager
    def locked(self):
        lock = self.file('.lock')
        try:
            descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as exc:
            raise ValueError('memory is busy; retry after the other writer finishes') from exc
        try:
            with os.fdopen(descriptor, 'wb') as stream:
                stream.write(encoded({'pid': os.getpid(), 'time': now()}))
            yield
        finally:
            lock.unlink()

    def load(self) -> dict:
        state = json.loads(self.file('state.json').read_bytes())
        if (not isinstance(state, dict) or state.get('schema_version') != 1 or type(state.get('revision')) is not int
                or state['revision'] < 0):
            raise ValueError('unsupported or malformed memory state')
        for data in [state['data'], *(h['data'] for h in state['history'])]:
            self.validate_data(data)
        for value in state['forgotten_ids']:
            identifier(value)
        if any(not HASH.fullmatch(h) for h in state['forgotten_hashes']):
            raise ValueError('invalid forgotten content hash')
        return state

    @staticmethod
    def validate_data(data: dict) -> None:
        if not isinstance(data, dict):
            raise ValueError('malformed memory data')
        if data['mode'] not in MODES:
            raise ValueError('invalid memory mode')
        if data.get('author_store') is not None and not isinstance(data['author_store'], str):
            raise ValueError('invalid author store path')
        for name in ('evidence', 'preferences', 'snapshots'):
            if not isinstance(data[name], dict):
                raise ValueError(f'invalid {name}')
            for key, record in data[name].items():
                if identifier(key) != record['id']:
                    raise ValueError('record identifier mismatch')
        for record in data['evidence'].values():
            if record['kind'] not in KINDS or record['purpose'] not in PURPOSES:
                raise ValueError('invalid evidence kind or purpose')
            if record['origin'] not in ('human', 'agent', 'mixed', 'unknown'):
                raise ValueError('invalid evidence origin')
            if record.get('author') is not None and not isinstance(record['author'], str):
                raise ValueError('author attribution must be a string or null')
            if record['origin'] == 'human' and not (record.get('author') or '').strip():
                raise ValueError('human evidence requires explicit author attribution')
            scope(record['scope'])
            for blob in record['blobs'].values():
                if not isinstance(blob, str) or not HASH.fullmatch(blob):
                    raise ValueError('invalid evidence content reference')
        for record in data['snapshots'].values():
            if not HASH.fullmatch(record['blob']):
                raise ValueError('invalid snapshot content reference')
        for pref in data['preferences'].values():
            if pref['status'] not in STATUSES or not isinstance(pref['text'], str) or not pref['text'].strip():
                raise ValueError('invalid preference')
            scope(pref['scope'])
            for field in ('support', 'counter'):
                if not isinstance(pref[field], list) or any(i not in data['evidence'] for i in pref[field]):
                    raise ValueError('preference references missing evidence')
            if not supported(pref, data['evidence']):
                raise ValueError('active preference lacks appropriate independent human evidence')

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
            state = {'schema_version': 1, 'revision': 0, 'history': [],
                     'forgotten_ids': [], 'forgotten_hashes': [],
                     'data': {'mode': mode, 'author_store': link,
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
        return {'store': str(self.path), 'revision': state['revision'], 'mode': state['data']['mode'],
                'author_store': state['data']['author_store'],
                'profile_edited': self.edited_profile(state)}

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
        state['history'] = (history if history is not None else
                            old['history'] + [{'revision': old['revision'], 'time': now(), 'data': old['data']}])
        if forgotten_ids is not None:
            state['forgotten_ids'] = forgotten_ids
        if forgotten_hashes is not None:
            state['forgotten_hashes'] = forgotten_hashes
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
            atomic_write(self.file('state.json'), encoded(state))
        except (OSError, ValueError):
            for path in created:
                path.unlink(missing_ok=True)
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
                  linked_author: Path | None = None, unlink: bool = False) -> dict:
        with self.locked():
            state = self.checked(revision)
            data = deepcopy(state['data'])
            if mode is not None:
                data['mode'] = mode
            if linked_author is not None:
                data['author_store'] = self.check_link(linked_author)
            if unlink:
                data['author_store'] = None
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
        if state['data']['mode'] != 'learn':
            return {**self.summary(state), 'candidate': None, 'reason': 'learning disabled'}
        matches = [s for s in state['data']['snapshots'].values() if s['source'] == source]
        previous = (state['data']['snapshots'].get(baseline) if baseline else
                    max(matches, key=lambda s: s['sequence']) if matches else None)
        if not previous or previous['source'] != source:
            return {**self.summary(state), 'candidate': None, 'reason': 'no matching baseline'}
        before = self.blob(previous['blob']).decode('utf-8')
        if before == after:
            return {**self.summary(state), 'candidate': None, 'reason': 'unchanged'}
        candidate = {'kind': 'observation', 'origin': 'unknown', 'author': None,
                     'purpose': 'unknown', 'scope': {}, 'lineage': source,
                     'source': source, 'baseline': previous['id'], 'before': before, 'after': after}
        return {**self.summary(state), 'candidate': candidate, 'alignment': 'whole-passage; not inferred',
                'diff': ''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                                                   fromfile='agent baseline', tofile='current text'))}

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
        with self.locked():
            state = self.checked(revision, learn=not author_request)
            data = deepcopy(state['data'])
            blobs, aliases = {}, {}
            for item in payload.get('evidence', []):
                entry = deepcopy(item)
                allowed = {'id', 'kind', 'origin', 'author', 'purpose', 'scope', 'lineage', 'source',
                           'baseline', 'before', 'after', 'feedback', 'request', 'context'}
                if not isinstance(entry, dict) or set(entry) - allowed:
                    raise ValueError('unsupported evidence fields')
                supplied_id = entry.pop('id', None)
                contents = {}
                for field in ('before', 'after', 'feedback', 'request', 'context'):
                    if field in entry:
                        value = entry.pop(field)
                        if not isinstance(value, str):
                            raise ValueError('evidence text must be a string')
                        raw = value.encode()
                        contents[field] = digest(raw)
                        blobs[digest(raw)] = raw
                if not contents or not any(blobs[h].strip() for h in contents.values()):
                    raise ValueError('evidence requires text')
                kind = entry.get('kind')
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
                entry['blobs'] = contents
                entry['content_hash'] = digest(encoded({k: v for k, v in contents.items()
                                                       if k in ('before', 'after', 'feedback')}))
                entry.setdefault('lineage', entry['source'] or entry['content_hash'])
                if not isinstance(entry['lineage'], str) or not entry['lineage']:
                    raise ValueError('evidence requires a nonempty lineage')
                fingerprint = digest(encoded(entry))
                duplicate = next((e for e in data['evidence'].values() if e['fingerprint'] == fingerprint), None)
                key = identifier(supplied_id or 'e-' + fingerprint[:24])
                if key in state['forgotten_ids'] or entry['content_hash'] in state['forgotten_hashes']:
                    raise ValueError('evidence was forgotten')
                if duplicate:
                    aliases[key] = duplicate['id']
                    continue
                if key in data['evidence']:
                    raise ValueError('evidence is immutable; use a new identifier')
                entry.update(id=key, fingerprint=fingerprint, time=now())
                data['evidence'][key] = entry
            for item in payload.get('preferences', []):
                pref = deepcopy(item)
                if not isinstance(pref, dict) or set(pref) - {'id', 'text', 'scope', 'status', 'support', 'counter'}:
                    raise ValueError('unsupported preference fields')
                key = identifier(pref['id'])
                if key in state['forgotten_ids']:
                    raise ValueError('preference was forgotten')
                pref.setdefault('scope', {})
                pref.setdefault('status', 'tentative')
                for field in ('support', 'counter'):
                    pref[field] = list(dict.fromkeys(aliases.get(i, i) for i in pref.get(field, [])))
                previous = data['preferences'].get(key)
                if previous and previous['status'] == 'explicit' and any(
                        pref[field] != previous[field] for field in ('text', 'scope', 'status')):
                    added = set(pref['support']) - set(previous['support'])
                    if not any(i in data['evidence'] and eligible(data['evidence'][i])
                               and data['evidence'][i]['kind'] == 'feedback' for i in added):
                        raise ValueError('changing an explicit preference requires new explicit author feedback')
                data['preferences'][key] = pref
            if data == state['data'] and profile_hash is None:
                return {**self.summary(state), 'aliases': aliases, 'duplicate': True}
            result = self.commit(state, data, blobs, profile_hash=profile_hash)
            return {**self.summary(result), 'aliases': aliases, 'duplicate': False}

    def show(self, key: str | None = None) -> dict:
        state = self.load()
        if key is None:
            return {**self.summary(state), 'data': state['data']}
        for name in ('evidence', 'preferences', 'snapshots'):
            if key in state['data'][name]:
                entry = deepcopy(state['data'][name][key])
                for field, blob in entry.get('blobs', {}).items():
                    entry[field] = self.blob(blob).decode('utf-8')
                if 'blob' in entry:
                    entry['content'] = self.blob(entry['blob']).decode('utf-8')
                return {**self.summary(state), 'record': entry}
        raise ValueError('memory record not found')

    def history(self) -> list:
        return [{'revision': h['revision'], 'time': h['time']} for h in self.load()['history']]

    def restore(self, revision: int, version: int) -> dict:
        with self.locked():
            state = self.checked(revision)
            match = next((h for h in state['history'] if h['revision'] == version), None)
            if match is None:
                raise ValueError('history version not found')
            data = deepcopy(match['data'])
            # Restoring prose memory cannot enable learning or switch author scope.
            for field in ('mode', 'author_store'):
                data[field] = state['data'][field]
            return self.summary(self.commit(state, data))

    def forget(self, revision: int, key: str) -> dict:
        with self.locked():
            state = self.checked(revision)
            if self.edited_profile(state):
                raise ValueError('reconcile the edited profile before forgetting; opaque manual text may contain the material')
            versions = [state['data'], *(h['data'] for h in state['history'])]
            if key not in state['forgotten_ids'] and not any(
                    key in d[n] for d in versions for n in ('evidence', 'preferences', 'snapshots')):
                raise ValueError('memory record not found')
            removed = {key}
            hashes = set(state['forgotten_hashes'])
            for data in versions:
                pref = data['preferences'].get(key)
                if pref:
                    removed.update(pref['support'] + pref['counter'])
            # Include duplicate/embedded payloads so whole-file snapshots cannot retain a deleted passage.
            needles = set()
            for data in versions:
                for name in ('evidence', 'snapshots'):
                    for item in data[name].values():
                        if item['id'] in removed:
                            refs = item.get('blobs', {}).values() if name == 'evidence' else [item['blob']]
                            for ref in refs:
                                value = self.blob(ref)
                                if value:
                                    needles.add(value)
                                    hashes.add(ref)
                            if name == 'evidence':
                                hashes.add(item['content_hash'])
            for path in self.file('text').glob('*.txt'):
                value = self.blob(path.stem)
                if any(needle in value for needle in needles):
                    hashes.add(path.stem)
            for data in versions:
                for name in ('evidence', 'snapshots'):
                    for item in data[name].values():
                        refs = item.get('blobs', {}).values() if name == 'evidence' else [item['blob']]
                        if any(ref in hashes for ref in refs):
                            removed.add(item['id'])
            def scrub(data):
                result = deepcopy(data)
                for name in ('evidence', 'preferences', 'snapshots'):
                    result[name] = {i: e for i, e in result[name].items() if i not in removed}
                for pref in result['preferences'].values():
                    for field in ('support', 'counter'):
                        pref[field] = [i for i in pref[field] if i not in removed]
                    if not supported(pref, result['evidence']):
                        pref['status'] = 'needs-review'
                    if any(needle.decode('utf-8') in pref['text'] for needle in needles):
                        pref['text'] = 'Preference needs review after supporting material was forgotten.'
                        pref['status'] = 'needs-review'
                for evidence in result['evidence'].values():
                    if evidence.get('baseline') in removed:
                        evidence['baseline'] = None
                for snapshot in result['snapshots'].values():
                    if snapshot['parent'] in removed:
                        snapshot['parent'] = None
                return result
            history = [{**h, 'data': scrub(h['data'])} for h in state['history']]
            history.append({'revision': state['revision'], 'time': now(), 'data': scrub(state['data'])})
            result = self.commit(state, scrub(state['data']), history=history,
                                 forgotten_ids=sorted(set(state['forgotten_ids']) | removed),
                                 forgotten_hashes=sorted(hashes))
            # Metadata no longer references these payloads. Also clean any orphaned pre-commit writes.
            used = set()
            for data in [result['data'], *(h['data'] for h in result['history'])]:
                used.update(s['blob'] for s in data['snapshots'].values())
                used.update(b for e in data['evidence'].values() for b in e['blobs'].values())
            for path in self.file('text').glob('*.txt'):
                if path.stem not in used:
                    self.file(f'text/{path.name}').unlink()
            return {**self.summary(result), 'forgotten': sorted(removed)}


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
        for pref in current_state['data']['preferences'].values():
            if pref['status'] in ('explicit', 'observed'):
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
        candidates = [p for p in current_state['data']['preferences'].values()
                      if p['status'] in ('explicit', 'observed')
                      and all(query.get(k) in values for k, values in p['scope'].items())]
        candidates.sort(key=lambda p: (p['status'] != 'explicit', -len(p['scope']), p['id']))
        for pref in candidates:
            entry = {'store': str(current.path), **pref}
            size = len(encoded(entry).decode())
            if size > remaining:
                result['warnings'].append(f"Preference omitted by budget: {pref['id']}")
                continue
            result['preferences'].append(entry)
            remaining -= size
            # Include counterexamples before positive examples when available.
            for key in pref['counter'] + pref['support']:
                choices.append((current, key))
    seen = set()
    for current, key in choices:
        if len(result['examples']) >= examples:
            break
        if (current.path, key) in seen:
            continue
        seen.add((current.path, key))
        entry = {'store': str(current.path), **current.show(key)['record']}
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
