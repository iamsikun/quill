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
    assert len(cases) == len({c['id'] for c in cases}) == 16
    assert sum(not c['expect_activation'] for c in cases) == 2
    for case in cases:
        assert case['must_preserve'] and case['must_not']
        for reference in case['references']:
            assert (runner.SKILL / 'references' / reference).is_file()
        # A grading-only sentinel must never enter a model prompt.
        graded = {**case, 'must_preserve': ['GRADING_SENTINEL'], 'must_not': ['GRADING_SENTINEL']}
        for arm in runner.ARMS:
            prompt = runner.build_prompt(graded, arm, 'codex')
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
