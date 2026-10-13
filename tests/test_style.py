from __future__ import annotations

import json
import hashlib
from pathlib import Path

import pytest

from quill import style
from quill.cli import main
from quill.skills import install_skill, uninstall_skill
from quill.style import StyleStore, author_store, default_store, digest, export_context, writing_context


@pytest.fixture
def store(tmp_path):
    memory = StyleStore(tmp_path / 'project/.quill/style')
    memory.init('learn')
    return memory


def feedback(key='e1', text='In introductions, explain the problem before naming the method.', **changes):
    return {'id': key, 'kind': 'feedback', 'origin': 'human', 'author': 'author-a',
            'purpose': 'exposition', 'feedback': text, **changes}


def preference(key='p1', **changes):
    return {'id': key, 'text': 'Explain the problem before the method.',
            'status': 'explicit', 'scope': {'section': ['introduction']}, 'support': ['e1'], **changes}


def seed(store):
    return store.record(store.load()['revision'], {'evidence': [feedback()], 'preferences': [preference()]})


def all_files(root):
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}


def test_disabled_by_default_and_unmanaged_discovery(tmp_path):
    project = tmp_path / 'project'
    memory = StyleStore(project / '.quill/style')
    assert memory.init()['mode'] == 'off'
    nested = project / 'drafts/intro'
    nested.mkdir(parents=True)
    assert default_store(nested) == memory.path
    assert not (project / 'paper').exists()
    assert not (project / '.quill/config.yaml').exists()
    assert (memory.path / '.gitignore').read_text() == '*\n'
    assert writing_context(memory)['preferences'] == []
    with pytest.raises(ValueError, match='disabled'):
        seed(memory)
    memory.configure(0, mode='apply')
    with pytest.raises(ValueError, match='disabled'):
        memory.snapshot(1, 'intro', b'text')
    assert memory.harvest('intro', b'other')['reason'] == 'learning disabled'


def test_plain_file_store_interoperates_without_cli_initialization(tmp_path):
    root = tmp_path / 'native-memory'
    (root / 'text').mkdir(parents=True)
    raw = b'Use concrete verbs.'
    key = hashlib.sha256(raw).hexdigest()
    (root / 'text' / f'{key}.txt').write_bytes(raw)
    (root / '.gitignore').write_text('*\n')
    def canonical_hash(value):
        return hashlib.sha256((json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + '\n').encode()).hexdigest()
    record = {'kind': 'feedback', 'origin': 'human', 'author': 'author', 'purpose': 'style',
              'source': '', 'baseline': None, 'scope': {}, 'lineage': 'native-feedback',
              'blobs': {'feedback': key}, 'content_hash': canonical_hash({'feedback': key})}
    record.update(fingerprint=canonical_hash(record), id='native', time='2026-10-13T12:00:00+00:00')
    native = {'schema_version': 1, 'revision': 1, 'history': [], 'forgotten_ids': [], 'forgotten_hashes': [],
              'data': {'mode': 'apply', 'author_store': None, 'snapshots': {}, 'evidence': {'native': record},
                       'preferences': {'verbs': {'id': 'verbs', 'text': 'Use concrete verbs.', 'scope': {},
                                                'status': 'explicit', 'support': ['native'], 'counter': []}}}}
    (root / 'state.json').write_text(json.dumps(native))
    # No Quill initialization/record helper created these ordinary files.
    store = StyleStore(root)
    assert writing_context(store)['preferences'][0]['text'] == 'Use concrete verbs.'
    store.configure(1, mode='learn')
    assert store.load()['data']['evidence']['native'] == record
    assert store.file('profile.md').is_file()


def test_fresh_instance_uses_profile_and_applies_scope(store):
    seed(store)
    fresh = StyleStore(store.path)
    assert writing_context(fresh, {'section': 'introduction'})['preferences'][0]['id'] == 'p1'
    assert writing_context(fresh, {'section': 'results'})['preferences'] == []
    assert writing_context(fresh)['preferences'] == []
    fresh.configure(1, mode='apply')
    assert writing_context(fresh, {'section': 'introduction'})['preferences']
    fresh.configure(2, mode='off')
    assert writing_context(fresh, {'section': 'introduction'})['preferences'] == []


def test_explicit_memory_edit_does_not_enable_automatic_learning(store):
    store.configure(0, mode='apply')
    result = store.record(1, {'evidence': [feedback()], 'preferences': [preference()]}, author_request=True)
    assert result['mode'] == 'apply'
    assert writing_context(store, {'section': 'introduction'})['preferences']
    with pytest.raises(ValueError, match='attributed author feedback'):
        store.record(2, {'evidence': [{'kind': 'observation'}]}, author_request=True)
    with pytest.raises(ValueError, match='disabled'):
        store.snapshot(2, 'draft', b'not collected')


def test_scope_suggestions_do_not_silently_expand_a_preference(store):
    store.record(0, {'evidence': [feedback()],
                     'preferences': [preference(scope={'audience': ['economists']})]})
    context = writing_context(store, {'audience': 'economics'})
    assert not context['preferences']
    assert context['scope_options']['audience'] == ['economists']
    assert context['warnings']
    assert writing_context(store, {'audience': 'economists'})['preferences']


def test_author_linking_is_explicit_and_does_not_copy(tmp_path, monkeypatch):
    monkeypatch.setenv('XDG_CONFIG_HOME', str(tmp_path / 'config'))
    author = StyleStore(author_store('alice'))
    author.init('learn')
    seed(author)
    project = StyleStore(tmp_path / 'paper/.quill/style')
    project.init('apply', author.path)
    assert not project.load()['data']['preferences']
    context = writing_context(project, {'section': 'introduction'})
    assert context['preferences'][0]['store'] == str(author.path)
    project.configure(0, unlink=True)
    assert writing_context(project, {'section': 'introduction'})['preferences'] == []
    with pytest.raises(ValueError, match='different'):
        project.configure(1, linked_author=project.path)
    project.configure(1, linked_author=author.path)
    with pytest.raises(ValueError, match='unlinked'):
        author.configure(1, linked_author=project.path)


def test_project_precedes_author_and_missing_author_does_not_block(tmp_path):
    author = StyleStore(tmp_path / 'author')
    author.init('learn')
    seed(author)
    project = StyleStore(tmp_path / 'project')
    project.init('learn', author.path)
    seed(project)
    assert [p['store'] for p in writing_context(project, {'section': 'introduction'})['preferences']] == [str(project.path), str(author.path)]
    author.file('state.json').unlink()
    context = writing_context(project, {'section': 'introduction'})
    assert len(context['preferences']) == 1 and 'unavailable' in context['warnings'][0]


def test_exact_snapshot_lineage_and_external_revision_before_next_write(store):
    raw = b'Intuition.\r\n\r\n$\\alpha=1$; \\cite{smith}; \\ref{eq:a}.\r\n'
    first = store.snapshot(0, 'paper:intro', raw)
    assert store.show(first['snapshot']['id'])['record']['content'].encode() == raw
    assert store.snapshot(1, 'paper:intro', raw)['duplicate']
    changed = b'$\\alpha=1$; \\cite{smith}; \\ref{eq:a}.\r\n\r\nIntuition revised.\r\n'
    before = all_files(store.path)
    harvested = store.harvest('paper:intro', changed)
    assert all_files(store.path) == before
    candidate = harvested['candidate']
    assert candidate['before'].encode() == raw and candidate['after'].encode() == changed
    assert candidate['origin'] == 'unknown' and 'not inferred' in harvested['alignment']
    store.record(1, {'evidence': [candidate]})
    second = store.snapshot(2, 'paper:intro', b'Next agent output.')
    assert second['snapshot']['parent'] == first['snapshot']['id']
    evidence = next(iter(store.load()['data']['evidence']))
    assert store.show(evidence)['record']['after'].encode() == changed
    assert store.harvest('paper:intro', b'Next agent output.')['reason'] == 'unchanged'
    assert store.harvest('other', b'text')['reason'] == 'no matching baseline'


def test_duplicate_records_do_not_strengthen_preferences(store):
    seed(store)
    assert store.record(1, {'evidence': [feedback('alias')]})['duplicate']
    assert store.load()['revision'] == 1
    assert len(store.load()['data']['evidence']) == 1
    bad = preference(status='observed', support=['e1', 'alias'])
    with pytest.raises(ValueError, match='independent'):
        store.record(1, {'evidence': [feedback('alias')], 'preferences': [dict(bad, id='p2')]})


@pytest.mark.parametrize('origin,purpose,kind', [
    ('unknown', 'exposition', 'revision'), ('agent', 'style', 'revision'),
    ('human', 'scientific', 'revision'), ('human', 'style', 'observation'),
])
def test_inappropriate_evidence_cannot_establish_preferences(store, origin, purpose, kind):
    items = [{'id': f'e{i}', 'kind': kind, 'origin': origin, 'purpose': purpose, 'author': 'a',
              'before': f'Before {i}', 'after': f'After {i}', 'lineage': f'p{i}'} for i in (1, 2)]
    with pytest.raises(ValueError, match='independent'):
        store.record(0, {'evidence': items, 'preferences': [preference(status='observed', support=['e1', 'e2'])]})
    assert store.load()['revision'] == 0


def test_independent_revisions_and_tentative_observations(store):
    items = [{'id': f'e{i}', 'kind': 'revision', 'origin': 'human', 'purpose': 'exposition', 'author': 'a',
              'before': f'Before {i}', 'after': f'After {i}', 'lineage': f'p{i}'} for i in (1, 2)]
    store.record(0, {'evidence': items, 'preferences': [preference(status='observed', support=['e1', 'e2'])]})
    assert writing_context(store, {'section': 'introduction'})['preferences']
    store.record(1, {'preferences': [preference('tentative', status='tentative', support=['e1'])]})
    assert len(writing_context(store, {'section': 'introduction'})['preferences']) == 1


def test_coauthor_preferences_are_not_merged(store):
    items = [feedback('e1', 'My preference.', author='Ada'),
             feedback('e2', 'A second preference.', author='Bob')]
    with pytest.raises(ValueError, match='independent'):
        store.record(0, {'evidence': items, 'preferences': [preference(support=['e1', 'e2'])]})


def test_explicit_correction_requires_new_author_feedback(store):
    seed(store)
    narrowed = preference(scope={'section': ['methods']})
    with pytest.raises(ValueError, match='explicit author'):
        store.record(1, {'preferences': [narrowed]})
    correction = feedback('e2', 'That preference applies only to methods sections.')
    narrowed['support'] = ['e2']
    store.record(1, {'evidence': [correction], 'preferences': [narrowed]})
    assert not writing_context(store, {'section': 'introduction'})['preferences']
    assert writing_context(store, {'section': 'methods'})['preferences']


def test_stale_updates_and_live_lock_preserve_state(store):
    seed(store)
    before = all_files(store.path)
    with pytest.raises(ValueError, match='stale'):
        store.record(0, {'evidence': [feedback('e2', 'A new preference.')]})
    assert all_files(store.path) == before
    with store.locked():
        with pytest.raises(ValueError, match='busy'):
            store.configure(1, mode='off')
    assert all_files(store.path) == before


def test_failed_metadata_commit_cleans_unpublished_originals(store, monkeypatch):
    before = all_files(store.path)
    original = style.atomic_write
    def failing_write(path, content):
        if path.name == 'state.json':
            raise OSError('simulated disk failure')
        original(path, content)
    monkeypatch.setattr(style, 'atomic_write', failing_write)
    with pytest.raises(OSError, match='disk failure'):
        seed(store)
    assert all_files(store.path) == before


@pytest.mark.parametrize('payload', [
    {'unknown': []}, {'evidence': [{'kind': 'revision', 'before': 'only'}]},
    {'evidence': [feedback(author=None)]}, {'preferences': [preference(support=['missing'])]},
    {'preferences': [preference(id='../escape')]}, {'evidence': [feedback(scope={'bogus': ['x']})]},
])
def test_malformed_records_are_atomic(store, payload):
    before = all_files(store.path)
    with pytest.raises((ValueError, KeyError, TypeError)):
        store.record(0, payload)
    assert all_files(store.path) == before


def test_edited_profile_is_preserved_and_can_be_reconciled(store):
    seed(store)
    manual = b'# My correction\nUse this preference only in methods.\n'
    store.file('profile.md').write_bytes(manual)
    store.snapshot(1, 'passage', b'draft')
    assert store.file('profile.md').read_bytes() == manual
    context = writing_context(store, {'section': 'introduction'})
    assert context['manual_profiles'][0]['text'].encode() == manual
    assert not context['preferences']
    with pytest.raises(ValueError, match='reconcile'):
        store.forget(2, 'e1')
    with pytest.raises(ValueError, match='profile changed'):
        store.record(2, {}, profile_hash='wrong')
    store.record(2, {'evidence': [feedback('e2', 'Only in methods.')],
                     'preferences': [preference(scope={'section': ['methods']}, support=['e2'])]},
                 profile_hash=digest(manual))
    assert not store.show()['profile_edited']
    assert not writing_context(store, {'section': 'introduction'})['preferences']


def test_profile_edited_during_commit_is_preserved(store, monkeypatch):
    manual = b'# Author guidance\nKeep my new correction.\n'
    original = style.atomic_write
    def interleaved_write(path, content):
        original(path, content)
        if path.name == 'state.json':
            store.file('profile.md').write_bytes(manual)
    monkeypatch.setattr(style, 'atomic_write', interleaved_write)
    result = seed(store)
    assert result['profile_edited']
    assert store.file('profile.md').read_bytes() == manual


def test_restore_preserves_mode_and_history(store):
    seed(store)
    store.configure(1, mode='apply')
    store.restore(2, 0)
    assert store.show()['mode'] == 'apply'
    assert not store.show()['data']['preferences']
    store.restore(3, 1)
    assert store.show()['data']['preferences'] and store.show()['mode'] == 'apply'


def test_forget_scrubs_originals_duplicates_embedded_snapshots_and_history(store):
    secret = 'An unpublished personal example that must disappear.'
    store.record(0, {'evidence': [feedback(text=secret)], 'preferences': [preference()]})
    store.snapshot(1, 'paper', ('Some other text.\n' + secret + '\nMore context.').encode())
    store.record(2, {'evidence': [feedback('duplicate', secret, source='other')]})
    store.forget(3, 'e1')
    assert store.load()['data']['preferences']['p1']['status'] == 'needs-review'
    assert not store.load()['data']['snapshots']
    assert all(secret.encode() not in raw for raw in all_files(store.path).values())
    store.restore(4, 1)
    assert not store.load()['data']['evidence']
    with pytest.raises(ValueError, match='forgotten'):
        store.record(5, {'evidence': [feedback('new-id', secret)]})


def test_forget_retains_explicit_preference_with_independent_support(store):
    store.record(0, {'evidence': [feedback(), feedback('e2', 'Please also remember to start with the problem.')],
                     'preferences': [preference(support=['e1', 'e2'])]})
    store.forget(1, 'e1')
    assert store.load()['data']['preferences']['p1']['status'] == 'explicit'
    assert writing_context(store, {'section': 'introduction'})['preferences']


def test_forget_removes_quoted_source_from_derived_rules_and_can_retry(store):
    secret = 'Confidential phrase used in an author correction'
    store.record(0, {'evidence': [feedback(text=secret)],
                     'preferences': [preference(text='Avoid the wording: ' + secret)]})
    store.forget(1, 'e1')
    assert all(secret.encode() not in raw for raw in all_files(store.path).values())
    assert store.load()['data']['preferences']['p1']['status'] == 'needs-review'
    store.forget(2, 'e1')


def test_forget_does_not_delete_unrelated_evidence_with_empty_before(store):
    records = [{'id': name, 'kind': 'observation', 'before': '', 'after': text}
               for name, text in [('e1', 'private passage'), ('e2', 'unrelated passage')]]
    store.record(0, {'evidence': records})
    store.forget(1, 'e1')
    assert store.show('e2')['record']['after'] == 'unrelated passage'


def test_forget_preference_cannot_be_undone_by_restore(store):
    seed(store)
    store.forget(1, 'p1')
    store.restore(2, 1)
    assert not store.load()['data']['preferences'] and not store.load()['data']['evidence']
    with pytest.raises(ValueError, match='forgotten'):
        seed(store)


def test_context_budget_examples_and_export(store):
    items = [feedback(f'e{i}', f'Writing decision {i}') for i in range(6)]
    store.record(0, {'evidence': items, 'preferences': [preference(support=[e['id'] for e in items])]})
    context = writing_context(store, {'section': 'introduction'})
    assert len(context['examples']) == 3 and context['content_characters'] <= 8000
    assert writing_context(store, {'section': 'introduction'}, examples=0)['examples'] == []
    small = writing_context(store, {'section': 'introduction'}, budget=256)
    assert small['content_characters'] <= 256
    assert 'Explain the problem before the method.' in export_context(context)
    assert 'Scope:' in export_context(context)


def test_content_hash_integrity_and_symlink_protection(store, tmp_path):
    entry = store.snapshot(0, 'paper', b'original')['snapshot']
    store.file(f"text/{entry['blob']}.txt").write_bytes(b'corrupted')
    with pytest.raises(ValueError, match='hash mismatch'):
        store.show(entry['id'])
    outside = tmp_path / 'outside'
    outside.mkdir()
    alias = tmp_path / 'alias'
    alias.symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match='symlink'):
        StyleStore(alias)
    skill = tmp_path / 'skill'
    skill.mkdir()
    (skill / 'SKILL.md').write_text('instructions')
    with pytest.raises(ValueError, match='installed skill'):
        StyleStore(skill / 'memory')


def test_install_sync_and_uninstall_preserve_memory(store):
    project = store.path.parent.parent
    seed(store)
    before = all_files(store.path)
    install_skill(project, host='all', scope='project')
    install_skill(project, host='all', scope='project', sync=True)
    uninstall_skill(project, host='all', scope='project')
    assert all_files(store.path) == before


def test_cli_end_to_end_without_workspace(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    def command(*args):
        with pytest.raises(SystemExit) as stopped:
            main(['style', *args])
        assert stopped.value.code == 0, capsys.readouterr().err
        return capsys.readouterr().out
    assert json.loads(command('init', '--mode', 'learn'))['revision'] == 0
    payload = tmp_path / 'update.json'
    payload.write_text(json.dumps({'evidence': [feedback()], 'preferences': [preference()]}))
    command('record', '--input', str(payload), '--expected-revision', '0')
    assert json.loads(command('context', '--section', 'introduction'))['preferences']
    assert '# Portable Quill' in command('export', '--section', 'introduction')
    command('configure', '--mode', 'apply', '--expected-revision', '1')
    assert json.loads(command('show', 'p1'))['record']['id'] == 'p1'
    assert json.loads(command('history'))['history']
    command('forget', 'p1', '--expected-revision', '2')
    command('restore', '1', '--expected-revision', '3')
    assert not json.loads(command('show'))['data']['preferences']
