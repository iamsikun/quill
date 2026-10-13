from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('personalization_eval', ROOT / 'evals/personalization.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def test_grading_and_held_out_passages_do_not_leak_into_training():
    cases = json.loads((ROOT / 'evals/personalization.json').read_text())
    assert len(cases) == len({c['id'] for c in cases}) == 11
    for case in cases:
        case = {**case, 'grading': {'sentinel': 'GRADING_PRIVATE_SENTINEL'},
                'source': 'HELD_OUT_PRIVATE_SENTINEL'}
        training = runner.training_prompt(case)
        application = runner.application_prompt(case)
        assert 'GRADING_PRIVATE_SENTINEL' not in training + application
        assert 'HELD_OUT_PRIVATE_SENTINEL' not in training
        assert 'HELD_OUT_PRIVATE_SENTINEL' in application


def test_result_extraction_uses_final_agent_text():
    codex = '\n'.join(json.dumps(x) for x in [
        {'type': 'item.completed', 'item': {'type': 'command_execution', 'text': 'not prose'}},
        {'type': 'item.completed', 'item': {'type': 'agent_message', 'text': 'Progress commentary.'}},
        {'type': 'item.completed', 'item': {'type': 'agent_message', 'text': 'The final passage.'}},
    ])
    assert runner.final_text(codex) == 'The final passage.'
    claude = json.dumps({'type': 'result', 'result': 'A revised paragraph.'})
    assert runner.final_text(claude) == 'A revised paragraph.'


def test_learning_persists_between_separate_model_calls(monkeypatch):
    case = json.loads((ROOT / 'evals/personalization.json').read_text())[0]
    monkeypatch.setattr(runner.subprocess, 'run', lambda *a, **kw: SimpleNamespace(stdout='test-host'))
    profile = runner.EMPTY_PROFILE + '\n## Introductions\n- Start with the decision problem. (stated)\n'
    example = '## 2026-10-13 · feedback · exposition\nAuthor: Start with the decision problem.\n'
    calls = []
    def invoke(host, prompt, project, timeout):
        calls.append(prompt)
        if len(calls) % 2 == 1 and 'Writing session' in prompt:
            assert not (project / '.quill').exists()
            text = json.dumps({'profile': profile, 'examples': example})
        else:
            assert (project / '.quill/style/profile.md').read_text() == profile
            assert 'Start with the decision problem.' in prompt and 'hospital' in prompt
            text = 'A hospital must reserve capacity before demand is known.'
        return {'exit_code': 0, 'text': text, 'prompt': prompt}
    monkeypatch.setattr(runner, 'invoke', invoke)
    record = runner.run_case(case, 'codex', 'examples', 1)
    assert 'error' not in record and len(calls) == 2
    assert record['memory'] == {'profile': profile, 'examples': example}
    assert example in calls[1]
    reused = runner.run_case(case, 'codex', 'learned', 1, training_record=record)
    assert reused['training_reused'] and len(calls) == 3
    assert example not in calls[2] and reused['memory'] == record['memory']


def test_invalid_learning_update_is_reported(monkeypatch):
    case = json.loads((ROOT / 'evals/personalization.json').read_text())[0]
    monkeypatch.setattr(runner.subprocess, 'run', lambda *a, **kw: SimpleNamespace(stdout='test-host'))
    monkeypatch.setattr(runner, 'invoke', lambda *a: {'exit_code': 0, 'text': 'not json'})
    assert 'Invalid learning update' in runner.run_case(case, 'codex', 'learned', 1)['error']


def test_no_storage_case_does_not_try_to_train_or_create_store(monkeypatch):
    case = next(c for c in json.loads((ROOT / 'evals/personalization.json').read_text())
                if c['id'] == 'unavailable-storage')
    monkeypatch.setattr(runner.subprocess, 'run', lambda *a, **kw: SimpleNamespace(stdout='test-host'))
    def invoke(host, prompt, project, timeout):
        assert not (project / '.quill').exists()
        assert 'not saved' in prompt
        return {'exit_code': 0, 'text': 'The policy reduced processing time in the observed pilot.'}
    monkeypatch.setattr(runner, 'invoke', invoke)
    result = runner.run_case(case, 'claude', 'examples', 1)
    assert 'error' not in result and len(result['stages']) == 1


def test_model_sessions_remain_read_only():
    assert runner.command('codex')[runner.command('codex').index('--sandbox') + 1] == 'read-only'
    assert runner.command('claude')[-2:] == ['--tools', '']
