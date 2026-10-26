"""Structural drift checks for the review checklist. They do not establish prose quality."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills/quill'
CHECKLIST = (SKILL / 'references/checklist.md').read_text()
RULE = re.compile(r'^\*\*([A-Z]\d+) · ([^*]+)\.\*\*', re.M)
CITED = re.compile(r'\b([UAESDR]\d{1,2})\b')
RANGE = re.compile(r'\b([UAESDR])(\d{1,2})–\1?(\d{1,2})\b')


def rules() -> list[str]:
    return [match.group(1) for match in RULE.finditer(CHECKLIST)]


def test_rule_ids_are_unique_and_numbered_in_order():
    ids = rules()
    assert len(ids) == len(set(ids)) >= 30
    by_module: dict[str, list[int]] = {}
    for rule in ids:
        by_module.setdefault(rule[0], []).append(int(rule[1:]))
    assert set(by_module) == set('UAESDR')
    for numbers in by_module.values():
        assert numbers == list(range(1, len(numbers) + 1))


def test_every_rule_has_a_question_and_a_default_action():
    blocks = RULE.split(CHECKLIST)[1:]
    for rule, _title, body in zip(blocks[::3], blocks[1::3], blocks[2::3]):
        body = body.split('\n## ')[0]
        assert '?' in body, rule
        assert 'Default:' in body, rule


def test_cited_rule_ids_exist_everywhere_in_the_skill():
    ids = set(rules())
    for path in [SKILL / 'SKILL.md', *sorted((SKILL / 'references').glob('*.md'))]:
        text = path.read_text()
        cited = set(CITED.findall(text))
        for module, first, last in RANGE.findall(text):
            cited |= {f'{module}{n}' for n in range(int(first), int(last) + 1)}
        # Rule-like tokens such as "N1" are not used; anything matching must be a rule.
        assert cited <= ids, (path.name, sorted(cited - ids))


def test_routing_names_only_existing_modules_and_rules():
    routing = CHECKLIST.split('## Routing', 1)[1].split('\n## ', 1)[0]
    rows = [line for line in routing.splitlines() if line.startswith('| ') and '---' not in line][1:]
    assert rows
    ids, modules = set(rules()), {rule[0] for rule in rules()}
    for row in rows:
        cell = row.split('|')[2]
        for token in re.findall(r'\b[A-Z]\d*\b', cell):
            assert token in ids or token in modules, (row, token)
    assert any('AI-like' in row for row in rows)


def test_core_routes_to_review_and_natural_prose():
    core = (SKILL / 'SKILL.md').read_text()
    for reference in ('review.md', 'checklist.md', 'natural-prose.md'):
        assert f'references/{reference}' in core
    assert 'mandatory sequential passes' not in core
    assert 'pass the review' in core
    assert core.count('\n') < 250
