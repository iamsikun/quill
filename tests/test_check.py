from __future__ import annotations

import json
from pathlib import Path

import pytest

from quill.check import check_file, fidelity_guards, mask, style_candidates
from quill.cli import main
from quill.review import ReviewStore


@pytest.fixture
def project(tmp_path, monkeypatch):
    root = tmp_path / 'paper'
    root.mkdir()
    (root / '.git').mkdir()
    monkeypatch.setenv('XDG_CONFIG_HOME', str(tmp_path / 'config'))
    return root


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode())
    return path


def names(hits):
    return {(hit['rule'], hit['name']) for hit in hits}


def test_style_candidates_cover_review_patterns():
    text = ('We resample tasks, not models. Importantly, the bound holds.\n'
            'The profiles use the recorded dirty worktree at commit 3f2a9c1.\n'
            'The logarithmic scale displays every curve without truncation. % REVISED\n'
            'Method \\texttt{corrected\\_adaptive\\_gn} wins.\n'
            'Taken together, these results shed light on synthetic data. TODO\n')
    found = names(style_candidates(text))
    assert found >= {('E1', 'defensive contrast'), ('E3', 'scaffolding'), ('U5', 'commit or hash'),
                     ('U5', 'workflow narration'), ('U5', 'repair announcement'),
                     ('U5', 'placeholder or revision marker'), ('E6', 'code identifier'),
                     ('E2', 'generic wrap-up')}
    assert {hit['line'] for hit in style_candidates(text) if hit['rule'] == 'U5'} == {2, 3, 5}


def test_math_keys_and_comments_are_not_prose():
    text = ('The estimator $\\hat\\theta_n = x_i$ is consistent \\cite{smith_2020}, see\n'
            '\\ref{eq:main_result}. % note to self: worktree\n'
            '\\begin{equation}\na_b = c, not d\n\\end{equation}\n')
    assert style_candidates(text) == []
    assert len(mask(text)) == len(text) and mask(text).count('\n') == text.count('\n')


def test_markdown_percent_is_not_a_comment():
    hits = style_candidates('Error fell by 48% at commit 3f2a9c1.\n', latex=False)
    assert ('U5', 'commit or hash') in names(hits)


def test_effective_prose_produces_no_candidates():
    text = ('We randomly assigned 600 participants to one of three groups. '
            'The theorem does not establish finite-sample coverage, so we evaluate coverage '
            'in simulations with known means.\n')
    assert style_candidates(text) == []


def test_fidelity_guards_report_changed_tokens_and_scope():
    before = 'Intro stays.\n\nError fell by 48\\% \\cite{smith_2020}.\n\nWe have $x < 1$.\n'
    after = 'Intro stays.\n\nError fell by 50\\% \\cite{jones}.\n\nWe have $x \\le 1$.\n'
    guards = fidelity_guards(before, after, [(1, 1)])
    assert [g['paragraph'] for g in guards] == [2, 3]
    assert guards[0]['changes']['number'] == {'removed': ['48'], 'added': ['50']}
    assert guards[0]['changes']['citation']['added'] == ['\\cite{jones}']
    assert 'math' in guards[1]['changes'] and all(g['outside_span'] for g in guards)
    assert fidelity_guards(before, before) == []
    reworded = 'Intro stays.\n\nThe error fell by 48\\% \\cite{smith_2020}.\n\nWe have $x < 1$.\n'
    assert fidelity_guards(before, reworded, [(3, 3)]) == []


def test_profile_lint_patterns_are_candidates(project, tmp_path):
    write(tmp_path / 'config/quill/profile.md',
          "---\nmode: learn\nchecks:\n  - pattern: '[a-z]; [a-z]'\n    lesson: Avoid semicolons in prose.\n"
          "  - pattern: '('\n---\n# Writing profile\n")
    file = write(project / 'intro.tex', 'The bias falls; the variance rises. $a; b$\n')
    result = check_file(file)
    assert names(result['style']) == {('U7', 'profile: Avoid semicolons in prose.')}
    assert len(result['problems']) == 1
    assert check_file(file, profile=False)['style'] == []


def test_review_records_become_stale_after_edits(project):
    store = ReviewStore.for_project(project)
    file = write(project / 'sections/intro.tex', 'Reviewed text.\n')
    assert store.status([file]) == {'sections/intro.tex': {'state': 'no review'}}
    store.record(file, summary='Pass 1 and 2 complete')
    assert store.status()['sections/intro.tex']['state'] == 'current'
    assert (store.path / '.gitignore').read_text() == '*\n'
    write(file, 'Edited text.\n')
    assert store.status()['sections/intro.tex']['state'] == 'stale'
    store.record(file)
    record = json.loads(store.record_path('sections/intro.tex').read_text())
    assert len(record['history']) == 2 and store.status()['sections/intro.tex']['state'] == 'current'


def test_cli_check_and_review(project, monkeypatch, capsys):
    monkeypatch.chdir(project)

    def command(*args, code=0):
        with pytest.raises(SystemExit) as stopped:
            main(list(args))
        assert stopped.value.code == code, capsys.readouterr()
        return capsys.readouterr().out

    write(project / 'intro.tex', 'We use an instrument.\n\nThe effect was 4 points.\n')
    assert '0 style candidate(s)' in command('check', 'intro.tex')
    command('style', 'baseline', 'intro.tex')
    write(project / 'intro.tex', 'Importantly, we use an instrument.\n\nThe effect was 6 points.\n')
    output = command('check', 'intro.tex', '--baseline', '--lines', '1')
    assert 'E3 scaffolding' in output and 'number: -4 +6' in output
    assert 'outside the authorized lines' in output
    command('check', 'intro.tex', '--strict', code=1)
    assert json.loads(command('check', 'intro.tex', '--json'))[0]['style'][0]['rule'] == 'E3'
    command('review', 'status', 'intro.tex', code=1)
    assert 'review recorded: intro.tex' in command('review', 'record', 'intro.tex')
    assert 'intro.tex: current' in command('review', 'status')
    write(project / 'intro.tex', 'Changed.\n')
    assert 'stale' in command('review', 'status', code=1)


def test_hooks_remind_and_block_once_until_reviewed(project):
    from quill.hooks import run
    file = write(project / 'sections/intro.tex', 'Importantly, we use an instrument.\n')
    write(project / '.claude/skills/quill/SKILL.md', 'Skill.\n')
    edit = {'cwd': str(project), 'tool_name': 'Edit', 'tool_input': {'file_path': str(file)}}
    context = json.loads(run('post-edit', json.dumps(edit)))['hookSpecificOutput']['additionalContext']
    assert 'quill review record sections/intro.tex' in context and 'E3 scaffolding' in context
    skill = {**edit, 'tool_input': {'file_path': str(project / '.claude/skills/quill/SKILL.md')}}
    assert run('post-edit', json.dumps(skill)) == ''
    stop = {'cwd': str(project), 'stop_hook_active': False}
    assert json.loads(run('stop', json.dumps(stop)))['decision'] == 'block'
    assert run('stop', json.dumps({**stop, 'stop_hook_active': True})) == ''
    ReviewStore.for_project(project).record(file)
    assert run('stop', json.dumps(stop)) == ''
    write(file, 'Changed again.\n')
    assert json.loads(run('stop', json.dumps(stop)))['decision'] == 'block'
    assert run('stop', 'not json') == ''


def test_hook_without_edits_allows_stop(project):
    from quill.hooks import run
    assert run('stop', json.dumps({'cwd': str(project)})) == ''
