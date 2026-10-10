# Quill behavioral evaluation

The 21 cases in `cases.json` are synthetic and are not excerpts from the user's
paper. Expected properties are withheld from the model. They test fidelity and
scope before style preference; none requires research access or real manuscript data.
Five cases additionally test earned confidence: over-hedging, defensive conceptual
framing, redundant caveats, positioning with incomplete evidence, and observations
whose proposed mechanisms remain uncertain.

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

For repeated comparisons of instruction revisions, freeze each skill version and
use identical cases, runner, host configuration, and output budget. Choose sample
counts and scoring criteria before generating answers. Run the unchanged runner
from each snapshot, using a separate output directory per revision and sample;
interleave versions to reduce ordering effects. Conceal revision, arm, and sample
labels during scoring. Retain every sample and report counts per case and arm,
including ties and failures; do not stop sampling at the first passing answer.
Use controls that require legitimate clarification or critique when testing
whether a change reduces unsolicited advice.

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

Record fidelity and rhetorical effectiveness separately. The optional
`rhetorical_checks` lists specify case-level writing goals; they are grading-only,
like `must_preserve` and `must_not`, and must not enter model prompts. A faithful
answer can still be unnecessarily defensive. Conversely, a compelling answer
that invents a result fails fidelity.

For fidelity-passing outputs, conceal the arm labels and compare reader effort:
can a reader recover the claim, reasoning, supporting evidence, conditions, and
meaning of the quantities? Use the case's rhetorical checks, when present, to
assess directness, conceptual positioning, useful qualifications, and the
distinction between observations and explanations. Record preference or tie, plus
a short reason. Do not use hedge counts as a quality threshold, reward confidence
unsupported by the evidence, or require an exact reference answer. Preserve ties
and do not reward changes to already effective prose. Use human readers before
making claims about human comprehension. Structural tests establish fixture and
prompt integrity, not writing quality; automated checks and model judgments are
preliminary evidence only.

Record unavailable authentication, host failures, model identity when returned,
tool behavior, and incomplete cases separately. Do not count them as passing or
failing prose. Retain baseline ties. This small synthetic suite does not establish
superiority or generalization; use held-out manuscripts and accepted expert
revisions for subsequent evaluation.

See [the development results](RESULTS.md) for the completed comparison, targeted
followups, discovery evidence, remaining failures, and untested configurations.
