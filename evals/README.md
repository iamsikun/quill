# Quill behavioral evaluation

The 16 cases in `cases.json` are synthetic and are not excerpts from the user's
paper. Expected properties are withheld from the model. They test fidelity and
scope before style preference; none requires research access or real manuscript data.

## Three-arm comparison

Run each case in a fresh conversation with the same host/model configuration and
output budget:

- `plain`: the request and source only.
- `core`: add the Quill core instructions; do not load references.
- `references`: add the core and only the case's relevant references.

`run.py` runs one case/arm at a time and records the exact prompt, host command,
response, source hashes, exit status, elapsed time, and CLI version in a supplied output directory.
It uses a disposable project, never the user's manuscript. It requires an already
authenticated CLI. No API keys or model overrides are embedded. For example:

```bash
uv run python evals/run.py --host claude --arm plain --case theorem --output /tmp/quill-eval
uv run python evals/run.py --host claude --arm core --case theorem --output /tmp/quill-eval
uv run python evals/run.py --host claude --arm references --case theorem --output /tmp/quill-eval
```

Comparison arms supply all inputs inline and request returned text rather than
file writes. Claude's safe mode and disabled tools prevent incidental skill
loading. Codex uses read-only, ephemeral sessions and is asked not to use tools;
its built-in/user skill metadata may still be visible. Record that limitation when
interpreting comparisons. Model output alone is not evidence of skill discovery.

## Discovery

The `implicit` and `explicit` arms install a project-local skill in a disposable
project and use the normal skill-enabled host. The implicit request never names
Quill; the explicit request selects it. Keep tool traces and check actual skill
invocation or a read of its `SKILL.md`; self-report alone is inconclusive. Also run
the two negative cases and inspect for unwanted activation. Review-only fixture
files must remain unchanged. These arms may read files but must not write them.

```bash
uv run python evals/run.py --host codex --arm implicit --case clear-prose --output /tmp/quill-discovery
uv run python evals/run.py --host claude --arm explicit --case clear-prose --output /tmp/quill-discovery
```

## Scoring

First inspect each output against `must_preserve` and `must_not` in the case. Any
consequential changed claim, number, condition, unit, citation, or authorized scope
fails fidelity. Do not compensate for it with a high style rating.

For fidelity-passing outputs, conceal the arm labels and compare reader effort:
can a reader recover the claim, reasoning, supporting evidence, conditions, and
meaning of the quantities? Record preference or tie, plus a short reason. Do not
reward changes to already effective prose or insist on an exact reference answer.
Use human readers before making claims about human comprehension. Automated checks
and model judgments are preliminary evidence only.

Record unavailable authentication, host failures, model identity when returned,
tool behavior, and incomplete cases separately. Do not count them as passing or
failing prose. Retain baseline ties. This small synthetic suite does not establish
superiority or generalization; use held-out manuscripts and accepted expert
revisions for subsequent evaluation.

See [the development results](RESULTS.md) for the completed comparison, targeted
followups, discovery evidence, remaining failures, and untested configurations.
