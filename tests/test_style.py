from __future__ import annotations

from pathlib import Path

import pytest

from quill.cli import main
from quill.skills import install_skill, uninstall_skill
from quill.style import StyleStore, compare, default_store


@pytest.fixture
def project(tmp_path):
    root = tmp_path / 'paper'
    root.mkdir()
    (root / '.git').mkdir()
    return root


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode())
    return path


def test_baseline_creates_ignored_store_and_keeps_exact_bytes(project):
    store = StyleStore(default_store(project))
    raw = 'Intuition.\r\n\r\n$\\alpha=1$; \\cite{smith}; \\ref{eq:a}.\r\n'
    file = write(project / 'sections/intro.tex', raw)
    assert store.baseline(file) == 'sections/intro.tex'
    assert (store.path / '.gitignore').read_text() == '*\n'
    assert (store.path / 'baselines/sections/intro.tex').read_bytes() == raw.encode()
    assert store.changes() == {}


def test_changes_pair_edited_paragraphs_and_flag_substance(project):
    store = StyleStore(project / '.quill/style')
    file = write(project / 'paper.tex',
                 'Opening stays.\n\nWe introduce the estimator next. It uses repeated measurements.\n\n'
                 'The effect was 5 percent \\citep{a}.\n\n\\begin{equation}\ny = x\n\n\\end{equation}\n\nClosing stays.\n')
    store.baseline(file)
    write(file, 'Opening stays.\n\nRepeated measurements separate signal from noise; we build the estimator on them.\n\n'
                'The effect was 2 percent \\citep{a,b}.\n\n\\begin{equation}\ny = x\n\n\\end{equation}\n\nClosing stays.\n')
    style, substance = store.changes()['paper.tex']
    assert style['before'].startswith('We introduce') and style['after'].startswith('Repeated')
    assert style['touches'] == [] and style['context'][0] == 'Opening stays.'
    assert set(substance['touches']) == {'number', 'citation'}


def test_changes_keep_splits_together_and_detect_moves():
    split = compare('First.\n\nOne long paragraph to split.\n', 'First.\n\nOne long\n\nparagraph, split.\n')
    assert len(split) == 1 and split[0]['after'] == 'One long\n\nparagraph, split.\n'
    moved = compare('First idea stated plainly.\n\nSecond idea explained.\n\nThird.\n',
                    'Second idea explained.\n\nFirst idea stated plainly.\n\nThird.\n')
    assert moved and all(c['moved'] for c in moved)


def test_changes_report_missing_baseline_and_removed_file(project):
    store = StyleStore(project / '.quill/style')
    file = write(project / 'a.tex', 'Text.\n')
    assert store.changes([file]) == {'a.tex': 'no baseline'}
    store.baseline(file)
    file.unlink()
    assert store.changes() == {'a.tex': 'file removed'}


def test_files_outside_the_project_are_refused(project, tmp_path):
    store = StyleStore(project / '.quill/style')
    with pytest.raises(ValueError, match='outside the project'):
        store.baseline(write(tmp_path / 'elsewhere.tex', 'Text.\n'))


def test_moved_project_keeps_baselines(project, tmp_path):
    StyleStore(project / '.quill/style').baseline(write(project / 'intro.tex', 'Draft.\n'))
    moved = tmp_path / 'moved'
    project.rename(moved)
    write(moved / 'intro.tex', 'Revised.\n')
    assert StyleStore(default_store(moved)).changes()['intro.tex'][0]['after'] == 'Revised.\n'


def test_store_is_found_from_a_subdirectory(project):
    (project / '.quill/style').mkdir(parents=True)
    nested = project / 'sections/drafts'
    nested.mkdir(parents=True)
    assert default_store(nested) == (project / '.quill/style').resolve()


def test_install_sync_and_uninstall_preserve_memory(project):
    store = StyleStore(project / '.quill/style')
    store.baseline(write(project / 'intro.tex', 'Draft.\n'))
    write(store.path / 'profile.md', '---\nmode: learn\n---\n# Writing profile\n')
    before = {p: p.read_bytes() for p in store.path.rglob('*') if p.is_file()}
    install_skill(project, host='all', scope='project')
    install_skill(project, host='all', scope='project', sync=True)
    uninstall_skill(project, host='all', scope='project')
    assert {p: p.read_bytes() for p in store.path.rglob('*') if p.is_file()} == before


def test_cli_baseline_and_changes(project, monkeypatch, capsys):
    monkeypatch.chdir(project)
    def command(*args):
        with pytest.raises(SystemExit) as stopped:
            main(['style', *args])
        assert stopped.value.code == 0, capsys.readouterr().err
        return capsys.readouterr().out
    write(project / 'intro.tex', 'We use an instrument.\n\nThe effect was 4 points.\n')
    assert 'baseline saved: intro.tex' in command('baseline', 'intro.tex')
    assert 'No changes' in command('changes')
    write(project / 'intro.tex', 'Shipping costs shift prices, so we use them as an instrument.\n\nThe effect was 6 points.\n')
    output = command('changes')
    assert 'intro.tex: 2 change(s)' in output and 'changed number' in output
    assert 'Quill:  We use an instrument.' in output
