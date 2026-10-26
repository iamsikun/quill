from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('quill_eval', ROOT / 'evals/run.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def test_cases_and_prompts_keep_grading_separate():
    cases = json.loads((ROOT / 'evals/cases.json').read_text())
    assert len(cases) == len({c['id'] for c in cases}) == 44
    assert sum(not c['expect_activation'] for c in cases) == 2
    issues = {c['id'] for c in cases if c.get('issue')}
    assert {c['id'] for c in cases if c.get('rhetorical_checks')} == {
        'over-hedging', 'defensive-framing', 'redundant-caveats',
        'ambitious-positioning', 'observation-mechanism',
    } | issues
    assert {n for c in cases for n in c.get('issue', [])} == {3, 4, 5}
    for case in cases:
        assert case['must_preserve'] and case['must_not']
        for reference in case['references']:
            assert (runner.SKILL / 'references' / reference).is_file()
        for supplied in case.get('supplied', []):
            assert (ROOT / 'evals' / supplied).is_file()
        # Every grading field stays private in every comparison/discovery arm.
        graded = {**case, **{
            field: [f'GRADING_SENTINEL_{field}']
            for field in ('must_preserve', 'must_not', 'rhetorical_checks', 'issue')
        }}
        for host in ('codex', 'claude'):
            for arm in runner.ARMS:
                prompt = runner.build_prompt(graded, arm, host)
                assert 'GRADING_SENTINEL' not in prompt
                assert case['prompt'] in prompt and case['source'] in prompt


def test_comparison_and_discovery_have_distinct_contexts():
    case = {'prompt': 'Polish the sentence.', 'source': 'An example.', 'references': ['editing.md']}
    core = (runner.SKILL / 'SKILL.md').read_text()
    reference = (runner.SKILL / 'references/editing.md').read_text()
    assert core not in runner.build_prompt(case, 'plain', 'claude')
    assert core in runner.build_prompt(case, 'core', 'claude')
    assert reference not in runner.build_prompt(case, 'core', 'claude')
    assert reference in runner.build_prompt(case, 'references', 'claude')
    assert core not in runner.build_prompt(case, 'implicit', 'claude')
    assert 'quill' not in runner.build_prompt(case, 'implicit', 'claude').lower()
    assert runner.build_prompt(case, 'explicit', 'claude').startswith('/quill\n')
    assert '$quill' in runner.build_prompt(case, 'explicit', 'codex')


def test_frozen_versions_skip_references_they_lack(tmp_path):
    frozen = tmp_path / 'skill'
    (frozen / 'references').mkdir(parents=True)
    (frozen / 'SKILL.md').write_text('FROZEN CORE')
    (frozen / 'references/editing.md').write_text('FROZEN EDITING')
    case = {'prompt': 'Edit.', 'source': 'Text.', 'references': ['editing.md', 'checklist.md']}
    prompt = runner.build_prompt(case, 'references', 'claude', frozen)
    assert 'FROZEN CORE' in prompt and 'FROZEN EDITING' in prompt
    assert (runner.SKILL / 'SKILL.md').read_text() not in prompt


def load_session_runner():
    import sys
    sys.path.insert(0, str(ROOT / 'evals'))
    spec = importlib.util.spec_from_file_location('quill_session', ROOT / 'evals/session.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_session_fixture_controls_and_scopes():
    session = load_session_runner()
    case_dir = ROOT / 'evals/sessions/creative-selection'
    case = json.loads((case_dir / 'session.json').read_text())
    paper = (case_dir / 'paper.md').read_text()
    parts = session.sections(paper)
    for turn in case['turns']:
        assert all(heading in parts for heading in turn['scope'])
        # Prompts never carry grading material.
        for failure in case['failures']:
            assert failure['problem'] not in turn['prompt']
    assert all(session.control_results(case['controls'], paper, paper).values())
    assert session.out_of_scope_changes(paper, paper, []) == []
    edited = paper.replace('Importantly, this is a two-step procedure.', '')
    assert session.out_of_scope_changes(paper, edited, ['## 1. Introduction']) == []
    assert session.out_of_scope_changes(paper, edited, ['## 3. Validation']) == ['## 1. Introduction']
    renamed = paper.replace('## 3. Validation', '## 3. Finite-sample validation')
    assert session.out_of_scope_changes(paper, renamed, ['## 3. Validation']) == []
    broken = paper.replace('87 campaigns', 'some campaigns').replace('v2.3', 'v2')
    results = session.control_results(case['controls'], paper, broken)
    assert not results['P4-replicate-limitation'] and not results['P5-snapshot-provenance']
    merged = paper.replace('The theorem does not establish finite-sample coverage of the corrected interval.',
                           'Theorem 1 does not bound the MSE or establish finite-sample coverage.')
    assert session.control_results(case['controls'], paper, merged)['P3-necessary-negation']
    dropped = paper.replace('The theorem does not establish finite-sample coverage of the corrected interval.', '')
    assert not session.control_results(case['controls'], paper, dropped)['P3-necessary-negation']
    assert {f['rule'][0] for f in case['failures']} <= set('UAESDR')
    paraphrased = paper.replace("borrows the honest half's estimate", "weights the held-out half's estimate", 1)
    assert session.control_results(case['controls'], paper, paraphrased)['P7-concept-explanation']


def test_session_trace_summary_detects_reads_subagents_and_cli():
    session = load_session_runner()
    trace = [
        {'type': 'tool_use', 'name': 'Read', 'input': {'file_path': '/x/.claude/skills/quill/references/checklist.md'}},
        {'type': 'tool_use', 'name': 'Agent', 'input': {'prompt': 'review'}},
        {'type': 'tool_use', 'name': 'Bash', 'input': {'command': 'quill check paper.md'}},
        {'type': 'command_execution', 'command': 'sed -n 1,80p .agents/skills/quill/references/review.md'},
    ]
    summary = session.trace_summary(trace)
    assert summary['skill_files_read'] == ['references/checklist.md', 'references/review.md']
    assert summary['subagent_calls'] == 1 and summary['quill_cli_calls'] == ['quill check paper.md']
    assert not summary['personal_profile_touched']
