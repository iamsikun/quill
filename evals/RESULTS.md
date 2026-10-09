# Development evaluation — 2026-10-09

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
