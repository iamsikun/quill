# Development evaluations

## Quill 0.6.0 release smoke check

The final skill with version metadata 0.6.0 passed one fresh `theorem` case using
the `references` arm in Claude Code 2.1.296 (`claude-opus-5-5[1m]`). The answer
preserved B1–B3, each fixed t in (0, 1), convergence in probability to V(t),
asymptotic scope, and the absence of a uniform guarantee. It returned only the
requested passage, and no tool calls were observed. The implementing assistant
reviewed the answer. [The sanitized record](results/0.6.0-smoke.json) retains the
prompt, answer, configuration, and source hashes. This is a release smoke check,
not evidence of general writing quality or automatic skill discovery.

## Quill 0.5.0 release smoke check

The final writing guidance with version metadata 0.5.0 passed one fresh `theorem`
case using the `references` arm in Claude Code 2.1.296. The response preserved
B1–B3, each fixed t in (0, 1), convergence in probability, asymptotic scope, and
the absence of a uniform guarantee. It returned only the requested polished
passage. The implementing assistant reviewed the answer.
[The sanitized record](results/0.5.0-smoke.json) includes the answer, configuration,
model, case hash, and skill hashes. This is a release smoke check, not evidence
of general writing improvement or automatic discovery rates.

## Delivery follow-up with repeated samples — 2026-10-10

The follow-up aligns drafting and editing references with the core delivery rule:
add a separate note only for a material issue still unresolved after the requested
text, and stop once the deliverables are accurate and complete. A limitation
already explained in a requested reviewer response does not need a third author
note. Information unnecessary to the current claim does not automatically require
more analysis or commentary. Genuine evidence conflicts and explicit critique
requests remain in scope.

We froze the preceding earned-confidence refinement as `before`, and the delivery
alignment as `after`. These are two unreleased instruction versions, not a
comparison against the published 0.4.2 skill. Four unchanged cases were run in both
`core` and `references` arms, with **three fresh samples per case, arm, and version**:
48 sessions. Versions were interleaved in a fixed shuffled order; all samples were
retained. The runner, task prompts, sources, 350-word limit, and Claude configuration
were identical. Claude Code 2.1.296 reported `claude-opus-5-5` in responses. All
processes completed; no tool calls were observed and review-only fixtures remained
unchanged.

A fixed rubric was recorded before generation and withheld from the writing model.
Two independent model assessors scored anonymous answers: one assessed both
regressions, the other both controls. Revision, arm, and sample labels were revealed
only after all scores were saved. Scientific fidelity includes factual assertions
in editorial advice. Requested-output discipline is separate: **2** fits the
request, **1** is usable with cleanup, and **0** misses the request. Necessary
clarification and requested critique are appropriate outputs, not unwanted advice.

| Case | Arm | Fidelity before | Fidelity after | Discipline 2 before | Discipline 2 after |
|---|---|---|---|---|---|
| Draft from evidence | Core | 3/3 | 3/3 | 1/3 | 3/3 |
| Draft from evidence | References | 2/3 | 3/3 | 2/3 | 2/3 |
| Reviewer feedback | Core | 3/3 | 3/3 | 1/3 | 3/3 |
| Reviewer feedback | References | 3/3 | 2/3 | 3/3 | 3/3 |
| Conflicting sources | Core | 3/3 | 2/3 | 1/3 | 2/3 |
| Conflicting sources | References | 2/3 | 2/3 | 0/3 | 1/3 |
| Review only | Core | 3/3 | 3/3 | 2/3 | 3/3 |
| Review only | References | 3/3 | 3/3 | 3/3 | 3/3 |

The two regression cases had unsolicited additions in 5/12 before outputs and
1/12 after outputs. Both fidelity and discipline passed in 6/12 before outputs
and 10/12 after outputs. The remaining delivery failure was a reference-arm results
paragraph followed by unnecessary advice about adding Monte Carlo standard errors.
One revised reference-arm reviewer response invented the claim that the synthetic
design does not vary industry; brevity did not prevent this fidelity failure.

All conflict answers identified the discrepancy, and all review-only answers
provided critique without rewriting the passage. The controls therefore did not
show suppression of legitimate clarification or review. However, conflict outputs
often added unnecessary hypothetical branches. Three such answers (one before,
two after) also falsely implied that a cross-reference automatically keeps two
separately written values consistent; both after answers proposed retaining 0.3
without sufficient confirmation. The before results case additionally produced
one answer that turned missing supplied variance estimates into uncomputed ones
and misdescribed an arithmetic reduction. These failures are retained, not counted
as successful writing because of fluent or concise presentation.

This is a partial improvement in these sampled tasks, not a clean pass or proof
of general reliability. Three samples per cell are too few to attribute the
observed fidelity differences to the instruction change. The assessments are
model judgments with no independent human or inter-rater validation. No additional
sampling was used to obtain a passing answer, and no cases or scoring criteria were
changed after seeing outputs.

[The complete sanitized record](results/2026-10-10-delivery-regressions.json)
contains the prospective rubric, all 48 outputs and judgments, per-case counts,
run order, prompts' hashes, case and instruction snapshots, and host configuration.
Raw account and session metadata are excluded. The earlier 49-session evaluation
below remains unchanged as historical evidence.

## Earned-confidence revision — 2026-10-10

These runs evaluated a development revision on top of 0.4.2 before the 0.5.0
version bump. Five new synthetic
cases cover over-hedging, defensive framing, redundant caveats, ambitious
positioning with incomplete evidence, and observations with uncertain mechanisms.
The suite now contains 21 cases; the historical runs below retain their original
16-case scope.

The initial comparison ran all five additions in `plain`, `core`, and `references`
arms (15 sessions), plus `theorem`, `association`, `draft-evidence`,
`reviewer-feedback`, `clear-prose`, and `surgical` in both skill arms (12 sessions).
After one instruction refinement, all 22 skill-arm sessions were rerun. The five
plain outputs were reused unchanged, for **49 new sessions** in total.

All sessions completed using Claude Code 2.1.296 with the response model reported
as `claude-opus-5-5`, the same CLI defaults, and no model override. The runner used
disposable projects, a 350-word limit, and disabled tools and slash commands; no
tool calls were observed. All outputs preserved fixture files. Process success
is separate from the writing judgments below.

A separate model assessor reviewed each round with arm labels concealed. Each
assessor received only the requests, sources, grading criteria, and anonymous
answers. Scientific fidelity was judged before rhetorical effectiveness; ties
were allowed. The implementing assistant then inspected the judgments and
revealed the labels. These are preliminary model judgments, not human validation.

| Skill outputs | Initial fidelity | Initial rhetoric | After refinement: fidelity | After refinement: rhetoric |
|---|---|---|---|---|
| Five new cases, both skill arms | 8/10 | 8 pass; 2 not assessed | 10/10 | 10/10 |
| Six regression cases, both skill arms | 12/12 | 9/12 | 12/12 | 10/12 |

Both initial skill answers in `ambitious-positioning` omitted the supplied status
that comparative experiments were planned but unrun. They did not fabricate
results; they failed the case's required preservation of material evaluation
status. The source supplied this status, though the request to sharpen positioning
did not separately demand that every planning detail be restated. The refinement
clarifies the distinction between implementation and evaluation without requiring
a catalogue of absent results. Both follow-up answers retained the planned status.

The initial `draft-evidence` answers and core `reviewer-feedback` answer also
added excessive unsolicited advice. The refinement keeps routine fidelity checks
in working reasoning and discourages lists of claims that a precisely scoped
finding never makes. A delivery weakness remains: the final `references` answers
for `draft-evidence` and `reviewer-feedback` still appended unnecessary commentary.
They passed fidelity but failed rhetorical restraint; the record retains both.

The plain baseline passed fidelity and rhetoric on all five new cases. In the
final comparison, the assessor preferred both skill arms on conceptual framing,
caveat consolidation, and positioning, and retained three-way ties on over-hedging
and observation versus mechanism. This does not establish superiority: there was
one sample per case and arm, refinements used the observed failures, and assessors
differed between rounds. No released-Quill control, held-out manuscript, human
comprehension study, or new discovery test was run.

[The sanitized record](results/2026-10-10-earned-confidence.json) preserves all
49 answers, initial failures, separate fidelity/rhetoric judgments, blinded
preferences, commands, source and prompt hashes, fixture snapshots, and the two
instruction versions. Raw host metadata and account/session identifiers are
excluded. Unchanged baseline answers are identified as reused in the follow-up.

## Quill 0.4.2 release smoke check

The unchanged writing guidance (with version metadata 0.4.2) passed one fresh
`theorem` case using the `references` arm in Claude Code 2.1.296. The response
preserved B1–B3, each fixed t in (0, 1), convergence in probability, asymptotic
scope, and the absence of a uniform guarantee. The implementing assistant reviewed
the answer. [The sanitized record](results/0.4.2-smoke.json) includes the answer,
model, case hash, and skill hashes. This is a release smoke check, not new evidence
of writing-quality improvements or automatic discovery rates.

## Quill 0.4.1 release smoke check

The unchanged writing guidance (with version metadata 0.4.1) passed one fresh
`theorem` case using the `references` arm in Claude Code 2.1.296. The response
preserved B1–B3, each fixed t in (0, 1), convergence in probability, asymptotic
scope, and the absence of a uniform guarantee. The implementing assistant reviewed
the answer. [The sanitized record](results/0.4.1-smoke.json) includes the answer,
model, case hash, and skill hashes. This is a release smoke check, not new evidence
of writing-quality improvements or automatic discovery rates.

## Quill 0.4.0 release smoke check

The unchanged writing guidance (with version metadata 0.4.0) passed one fresh
`theorem` case using the `references` arm in Claude Code 2.1.296. The response
preserved B1–B3, each fixed t in (0, 1), convergence in probability, asymptotic
scope, and the absence of a uniform guarantee. The implementing assistant reviewed
the answer. [The sanitized record](results/0.4.0-smoke.json) includes the answer,
model, case hash, and skill hashes. This is a release smoke check, not new evidence
of writing-quality improvements or automatic discovery rates.

## Earlier development comparison

These runs predate the rename from Pepper to Quill. Names, prompts, responses, and
hashes are retained as historical evidence, with the original cases archived at
[2026-10-09-cases.json](results/2026-10-09-cases.json). They do not independently
verify discovery under the new name. The current runner and cases use Quill.

The initial skill was exercised on all 16 synthetic cases in three arms: plain
prompt, core, and core plus relevant references (48 fresh Claude sessions).
Eight targeted followups tested a core refinement. Ten additional sessions checked
discovery in Codex and Claude. All recorded runs completed successfully as
processes; that does **not** mean every writing response passed.

[Sanitized results](results/2026-10-09.json) retain the final answers, per-output
fidelity judgments, initial preferences, core revisions, source hashes, and
selection evidence. These are judgments by the implementing assistant, not an
independent human assessment. Initial outputs were compared with arm labels
concealed; followups were unblinded. There was one sample per case and arm.

## Meaning before style

The initial comparison exposed consequential unsupported inferences:

| Case | Plain prompt | Core | With references |
|---|---|---|---|
| Association | Added “rates” to an unspecified outcome | Preserved outcome | Added “rates,” then flagged the assumption |
| Bias versus error | Added an unsupported practical recommendation | Preserved distinction | Preserved distinction |
| Practical inputs | Invented a tuning rule and evaluation claim | Preserved limits | Preserved limits |
| Caption | Assumed higher rates are preferable | Preserved sign and units | Preserved sign and units |
| Conflicting sources | Invented the parameter's role | Flagged conflict | Flagged conflict |
| Draft from evidence | Turned “not supplied” into “not computed” | Preserved evidence limits | Preserved evidence limits |
| Literature comparison | Inferred an identical dependence setting and coverage gap | Inferred an identical dependence structure | Compared only supported dimensions |
| Reviewer feedback | No fabricated completed analysis | Invented a property the design lacks | Grounded limitation |
| Optional style | Added an unsupported selection mechanism | Preserved distinction | Preserved distinction and used supplied profile |

Those unsupported inferences count as fidelity failures even when they appear in
otherwise fluent prose or in editorial commentary. The optional-style arms did
not have identical information: only the reference arm received the profile.
That case checks use of available context, not a fair comparison of style quality.

On the remaining cases, initial outputs preserved the essential scientific
claims. Delivery still varied. The plain prompt was best on the simple grammar
correction because it returned only the sentence. Both skill arms left already
clear prose unchanged, while the baseline rewrote it unnecessarily. Skill arms
handled the surgical paragraph boundary and review-only scope. Several answers
added dispensable notes, calculations, or placeholders; the recorded preferences
retain these weaknesses and ties.

The core was then refined to prohibit unsupported specificity and invented
limitations, distinguish missing supplied evidence from nonexistent analysis, and
avoid narrating routine edits. Both skill arms were rerun on mechanics,
association, literature comparison, and reviewer feedback. All eight preserved
scientific meaning in this review. Excess editorial commentary remained in some
outputs, including a singular alternative after the core-only grammar correction.
The other 12 cases were not rerun after the refinement. These are development
regressions, not held-out validation or proof that the errors cannot recur.

## Host discovery

| Host | Check | Observed result |
|---|---|---|
| Codex 0.153.4 | Natural-language polish | Confirmed read of project-installed `SKILL.md`; returned the clear sentence unchanged |
| Codex 0.153.4 | Explicit `$pepper`, theorem | Faithful answer; selection inconclusive because no separate load event was exposed |
| Codex 0.153.4 | Code and standalone-search negatives | No Pepper invocation/read observed |
| Claude Code 2.1.295 | Natural-language polish, theorem, review-only | Confirmed `Skill` calls selecting `pepper`; review fixture unchanged |
| Claude Code 2.1.295 | Explicit `/pepper`, polish | Pepper present in skill/command inventories and faithful answer; separate selection event not exposed |
| Claude Code 2.1.295 | Code and standalone-search negatives | No Pepper invocation/read observed |

Discovery used temporary project installations outside the Pepper checkout.
The user directories were not modified. Installation at both scopes is covered
mechanically; personal-scope discovery was not separately exercised. These few
observations do not establish an activation rate or guarantee natural-language
selection. Discovery used the initial core; its name, description, metadata, and
reference paths were unchanged by the refinement.

Claude reported `claude-opus-5-5[1m]` for comparisons and `claude-opus-5-5` for
discovery. Codex's JSON did not expose a model identifier. The full three-arm
comparison was **not run on Codex**. An initial Codex attempt could not write its
host state database under the parent sandbox; the recorded sessions used approved
host execution while retaining the child CLI's read-only workspace sandbox.

## Limits and next evidence

The fixtures contain invented research, not the user's manuscript. Comparison
arms supplied the inputs inline, disabled Claude tools and slash commands, and
requested no external access. One baseline nevertheless suggested access through
an institution absent from the input. That name is redacted in the saved answer;
host-context contamination or hallucination remains possible. Full isolation
from provider or account context cannot be assumed.

These results assess whether claims, reasoning, evidence, and conditions remain
recoverable from short passages. They do not measure human comprehension or
establish superiority over a strong plain prompt. Longer held-out manuscripts,
independent expert judgments, repeated sampling, and additional host/model
configurations remain untested.

## Personal writing memory — 2026-10-13

The [personalization smoke record](results/personalization-2026-10-13.json) retains
13 development samples from fresh Codex and Claude sessions. It links a compressed
archive of prompts, responses, source hashes, and execution metadata. No sample was
discarded. These are assistant-inspected synthetic cases, not author judgments.

The first positive Codex run exposed a retrieval miss: the model stored the audience
tag `economists`, while the task queried `economics`. Its fluent output did not
establish that personalization had been applied. Context retrieval now exposes
available scope tags for the agent to interpret, and fixtures use a shared vocabulary.
The subsequent positive run retrieved one preference and one supporting example.

The comparison set covers all eight scenarios. Inspection found appropriately scoped
explicit preferences, no generalized rule from the one-off instruction, no stylistic
lesson from the result correction, no author preference from an unattributed edit,
and no managerial-summary preference applied to technical methods. A corrected
preference controlled the later methods passage. Effective prose was returned
unchanged, and unavailable storage did not delay writing or elicit a persistence claim.

All four introduction arms—ordinary Quill, static profile, learned preferences,
and learned preferences with examples—began with the decision problem and preserved
the planned evaluation status. The latter two reused the same learned evidence.
This small comparison shows no writing-quality advantage; blind author preference
and revision effort remain unmeasured.

The harness persists validated updates between read-only sessions. It does not
establish automatic skill invocation, autonomous file-tool behavior, or support
in every host. Samples were captured during development; the archive preserves
each sample's instruction hashes and exact prompts rather than treating them as
a single frozen-version benchmark.

### Review fixes — 2026-10-13

The [follow-up record](results/personalization-2026-10-13-fixes.json) adds one Claude
sample for each new case. Two attributed revisions in independent passages of one
file produced an observed preference, which the held-out methods passage followed.
With conflicting coauthors, only the lead author's explicit preference became active.
A declared-author revision that corrected a number was classified as scientific and
taught no preference. That output preserved the finding but appended an unrequested
note, a remaining instance of over-commenting. Single samples with harness-managed
persistence do not test the agent-run snapshot/harvest loop or writing quality.

### Simplified memory — 2026-10-13

Memory was then reduced to an editable `profile.md`, an `examples.md` log, and
baselines for detecting the author's edits. The two records above used the earlier
JSON store and no longer describe the current workflow. The
[simplified-memory record](results/personalization-2026-10-13-simplified.json)
reruns all eleven cases once on Claude. Stated preferences were learned at once with
their scope and exceptions; one-off instructions, an unattributed edit, and
corrections of results were logged without becoming lessons; two independent
exposition edits produced a lesson. Every output preserved the findings, and no
session asked a question. One copyedit appended an unrequested “no corrections
needed” line. The harness does not exercise the agent-run `changes`/`baseline`
loop or the one-line notice of a profile change.

The profile then moved from the project to `~/.config/quill/` so that every agent
shares it. A spot check of `explicit-preference` and `repeated-pattern` (Claude,
examples arm) produced the same lessons in the new location; the other cases were
not rerun.

### Actual profile files and CLI — 2026-10-13

The [filesystem smoke record](results/host-memory-2026-10-13.json) and its compressed
tool archive retain all ten attempts, including two host startup failures, for 26
stage invocations. The final selected runs used Codex CLI 0.153.4 and Claude Code
2.1.296 with real file tools and this checkout's CLI. Each stage was a fresh session.

| Final check | Codex | Claude Code |
|---|---|---|
| Read and update an isolated shared profile; preserve author-owned text | Passed | Passed |
| Log a stated preference and its supporting feedback | Passed | Passed |
| Run `changes` before editing; detect two author edits and flag a corrected number | Passed | Passed |
| Learn the repeated style decision; preserve the corrected result and citation | Passed | Passed |
| Refresh a baseline matching the final manuscript | Passed | Passed |
| Apply the saved profile in another project and create its first baseline | Passed | Passed |

The tests exposed two instruction gaps. Codex omitted the first baseline in a new
project because the reference tied baseline creation to checking a previously
written file. One Claude sample saved a lesson without its source log. The reference
now requires baselines after every manuscript write with file learning enabled,
including the first write, and explicitly saves lessons with their evidence log.
The final profiles retained the stated estimation preference, learned the
condition-before-method pattern from two independent passages, and gained no style
lesson from the corrected number. The result, interval, and citation remained intact.

Codex needed approved host execution to initialize its state database, while its
child retained the workspace sandbox. Its configured model identifier was
unsupported by this CLI, so subsequent tests used CLI defaults without loading
user configuration. No user settings were changed. An initial Claude shell
allowlist blocked exploratory reads; later runs permitted shell tools in the
disposable test under the parent sandbox. An initial exact-phrase detector also
rejected a grammatical equivalent; that record is retained with the original check.

Profiles lived in an isolated `XDG_CONFIG_HOME` outside each project with access
granted explicitly. No personal profile or installed Quill was modified. The final
Codex prompt named the existing profile file explicitly after earlier conditional
reads yielded no profile output; the final read was verified in the tool trace.
The skill was also selected by explicit path. These are one-sample integration
smoke tests, not evidence of automatic discovery, denied-permission behavior, or
general writing improvement. The final reference hashes match the tested checkout.
