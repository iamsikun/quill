# Quill behavioral evaluation

The 44 cases in `cases.json` are synthetic and are not excerpts from the user's
paper. Expected properties are withheld from the model. They test fidelity and
scope before style preference; none requires research access or real manuscript data.
Five cases additionally test earned confidence: over-hedging, defensive conceptual
framing, redundant caveats, positioning with incomplete evidence, and observations
whose proposed mechanisms remain uncertain.

Twenty-three cases, marked with an `issue` field, test the guidance from issues
#3-#5 on held-out material in other domains:

- **Contribution hierarchy (#3):** connecting an abstract's contributions, keeping
  the main theorem prominent while preserving a rate condition, selecting evidence
  for an abstract, and respecting an author's deliberate relocation.
- **Reader path and displays (#4):** a theory-to-validation opening, false versus
  genuine concession and irrelevant versus necessary contrast, robustness versus
  fragility, a bias guarantee alongside a higher mean absolute error, expanding an
  explanation while trimming bookkeeping, a conclusion with competing messages, a
  table with grouped quantities and packed counts, and a protected model passage.
- **Natural prose (#5):** workflow narration with a real relocation destination,
  repair captions with a real clipping disclosure, unverified code labels, expert
  filler beside a modified construction, an overloaded name, an empty summary,
  repeated caveats across sections and a caption, an audit with passing passages,
  a multi-paragraph rewrite with formal and provenance controls, effective prose
  that should stay unchanged, and venue checklist text.

Each has `rhetorical_checks` that grade contribution clarity, continuity, or
directness separately from fidelity. Review-only and no-change controls are included.

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

To compare a frozen earlier version, pass its skill folder and a label, for example
`--skill /tmp/quill-0.6.0/skills/quill --label before`. A frozen version that lacks a
newer reference receives only the references it has; the record lists the missing ones.

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

## Personalization

`personalization.json` contains eleven simulated-author cases covering explicit
preferences, local instructions, factual corrections, unknown attribution, changed
audiences, corrected preferences, effective prose, unavailable storage, a pattern
repeated across independent passages, conflicting coauthors, and a declared-author
revision that mixes style with a corrected number. Training
feedback and held-out passages are separate. Grading fields never enter prompts.
These fixtures test the learning workflow; they are not real author judgments.

The separate `personalization.py` runner compares four arms:

- `none`: ordinary Quill.
- `static`: Quill plus a fixed profile (`fixtures/static-profile.md`) supplied as user context.
- `learned`: a model learns from the training session and returns the updated
  `profile.md` and `examples.md`; the harness saves them, and a fresh session
  receives the profile.
- `examples`: the same protocol; the fresh session also receives `examples.md`.

```bash
uv run python evals/personalization.py --host codex --arm examples --case explicit-preference --output /tmp/quill-personalization
uv run python evals/personalization.py --host claude --arm none --case explicit-preference --output /tmp/quill-personalization
```

All host sessions remain read-only and ephemeral. The runner owns a disposable
memory folder and reopens it between training and application. It saves exact
prompts, responses, skill hashes, host versions, learned memory, and failures.
Harness-managed persistence does **not** establish automatic skill discovery or
successful autonomous file-tool use. The existing comparison/discovery arms and
their restrictions are unchanged. Never run these cases against personal memory.

For a controlled learned-versus-examples comparison, freeze and reuse the same
learned evidence using `--training-record PATH` pointing to a previous matching
learned/examples result; the runner checks the case, skill hashes, and host.
Independent training runs can otherwise introduce another source of variation.
Retain all samples, including rejected updates and
empty learned profiles. The latter can be correct for a one-off or factual edit.

Grade fidelity first, then appropriateness of scope and attribution, application of
explicit corrections, unnecessary questions, false persistence claims, and author
revision effort. Model
judgments and synthetic author cases do not establish improved writing quality.
Use held-out manuscripts and blind author comparisons before claiming that benefit.

## Grading

`grade.py` grades blind. For single-turn cases it shuffles every answer to a case,
relabels them, and grades them together against the frozen
[case rubric](rubrics/cases.md); record names are attached only afterwards.
For sessions it grades one record at a time against the
[session rubric](rubrics/session.md), without the arm, skill, traces, or tool
evidence. Freeze the rubric before generating answers.

```bash
uv run python evals/grade.py cases /tmp/quill-eval/*.json --output /tmp/quill-grades.json
uv run python evals/grade.py session /tmp/quill-session/*.json --output /tmp/quill-session-grades.json
```

Model grades are preliminary evidence. Use blind human review before claiming
improved readability or comprehension.

## Long-session revision

Single prompts with tools disabled cannot show whether an agent skips the review,
forgets the guidance over many requests, or damages text while repairing it.
`session.py` runs one manuscript revision of six requests in a single host session
with file tools. The [fixture](sessions/creative-selection/) is a synthetic paper
with 27 embedded failures from issues #3-#5 and preservation controls: a theorem and
proposition that must stay verbatim, a necessary negation, a material limitation,
snapshot provenance, venue checklist text, a concept explanation, a clipping
disclosure, an effective paragraph, an appendix the user says to leave alone, and
every number. The requests revise sections in turn, remove AI-like writing, tighten
the abstract, review without editing, apply the review to one section, and render the
paper to the copy the user reads.

Arms are frozen skill versions and review configurations:

| Arm | Skill | Subagents | `quill` CLI |
|---|---|---|---|
| A | baseline (the reconciled skill before the review protocol) | no | no |
| B | A plus “review and revise twice against the guidance” | no | no |
| C | the structured review protocol | no | no |
| D | C | yes | no |
| E | C | yes | yes |
| F | C, with the opt-in `quill hook` post-edit and stop hooks (Claude only) | yes | yes |

B against C tests the protocol's structure, C against D the independent reviewer,
and D against E the deterministic checks. F was added after the first runs showed
that the review references were often not read (see the results). C also contains the new #3-#5 guidance,
so B against C does not separate structure from content.

```bash
uv run python evals/session.py --host claude --arm C --skill skills/quill --output /tmp/quill-session/claude-C-1.json
```

The runner isolates `XDG_CONFIG_HOME` so no personal profile is visible, shadows any
installed `quill` with a stub except in arm E, and records every turn's prompt, reply,
tool trace, and manuscript. Deterministic checks report edits outside each request's
sections, an unchanged file after the review-only request, each preservation control,
whether the user's copy matches a fresh rendering, skill files read, subagent calls,
CLI calls, and review records. Claude runs use restricted mode with file and shell
tools and no hooks or MCP servers. Codex runs use a workspace-write sandbox and resume
the same thread; Codex has no subagent tool here, so its D and E arms test only
the instructions and the CLI.

## Profile filesystem smoke test

`host_memory.py` exercises the actual file tools and CLI in three fresh sessions:
learn a stated preference and save a baseline; inspect two simulated author edits
and a corrected number, learn the repeated style decision, and refresh the baseline;
then apply the shared profile in another project and establish its first baseline.
The prompt identifies the existing profile path, and the hosts read its contents
from disk; the contents are not supplied in the prompt.

```bash
uv run python evals/host_memory.py --host codex --output /tmp/quill-codex-files.json
uv run python evals/host_memory.py --host claude --output /tmp/quill-claude-files.json
```

The runner copies this checkout's skill into disposable projects and puts a wrapper
for this checkout's CLI on `PATH`. An isolated `XDG_CONFIG_HOME` lives outside the
project and is granted local access; the user's installed Quill and personal profile
are untouched. Codex retains its workspace sandbox and uses CLI defaults without
loading user configuration. Claude uses restricted mode with file and shell tools
enabled, no connected MCP servers or hooks, and no interactive permission prompts.
The parent execution sandbox still applies; a CLI may need approval to initialize
its own host state before its child sandbox can run.

Records contain prompts, permitted host commands, tool evidence, before/after files,
and instrumented `changes`/`baseline` calls. Checks inspect actual artifacts and
command order, rather than accepting an agent's claim that it saved memory. Review
the learned lessons and scientific fidelity separately. This is an explicitly
selected skill smoke test with permitted storage, not an implicit discovery test,
a denied-permission test, or evidence of general writing improvement. Keep every
attempt, including setup failures and incomplete workflows.
