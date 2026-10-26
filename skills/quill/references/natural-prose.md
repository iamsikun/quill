# Natural scholarly prose

Technically careful prose can still read like an agent's work report: it defends
against objections nobody raised, narrates how it was checked, and closes with a
tidy summary. Finished scholarly prose tells the reader about the research. The
checks are E1–E9, U5, A8, and D4 in the [checklist](checklist.md). This file
explains how to apply them.

“AI-like” names an editorial concern, not a claim about authorship. Linguistic
patterns are not evidence of who wrote a passage, and a detector score is not a
measure of quality.

## Deciding what to do with a passage

For each suspect passage, ask what the intended reader needs to know there, then
**keep, delete, rewrite, or relocate** it within the authorized scope. Deletion and
relocation are normal outcomes. Replacing an unwanted sentence with a new, equally
generic one solves nothing. Leave effective prose unchanged.

When the passage reveals a substantive defect, such as a missing analysis, an
inaccurate method description, or an unsupported claim, smoother wording does not fix
it. Correct it within scope or flag it.

## Patterns

| Pattern | Example | Action |
|---|---|---|
| Defensive contrast (E1) | “This is an allocation guarantee, NOT a guarantee for the final estimator.” | State the result: “The theorem controls the selected allocation's population working risk.” Keep the conditions that extend it to final-estimator MSE if they govern interpretation. |
| Repeated scope disclaimers (A8) | An assumption stated with the theorem, then repeated after every result and in every caption. | Keep it where omission would mislead, including in a display read on its own. Delete the repetitions. |
| Workflow narration (U5) | “The profiles use the recorded dirty worktree at commit `<hash>`.” | Describe the implemented procedure. Move exact versions, uncommitted changes, commands, and hashes to the reproducibility documentation, if such a destination exists or is authorized. |
| Agent access limits as author facts (U5) | “Complete runtime records are unavailable in this local snapshot; row counts are not used as a substitute.” | If the document omits them: “Complete execution-time records are not provided.” What the agent's workspace lacks says nothing about what the authors have. When you cannot tell whether a limit belongs to the research or to your workspace, ask the author; do not restate it as a fact about the analysis. |
| Repair announcements in captions (D4) | “The logarithmic vertical scale displays every curve without truncation.” | “The vertical axes are logarithmic.” Keep real exclusions, censoring, or clipping. |
| Consistency assurances (D4) | “The curves and Table 4 use the same full-profile results.” | Delete it, or give the table's role: “Table 4 summarizes coverage across the evaluated settings.” Verify consistency without narrating it. |
| Code identifiers (E6) | `corrected_adaptive_gn`; “The row order corresponds to code identifiers.” | A verified display label such as “Adaptive plug-in.” Keep the mapping in code documentation. |
| Tutorial filler (E4) | “A nominal 95% procedure aims for 0.95,” or a textbook definition of a Wald interval, for statisticians. | Delete it if the audience knows it and it advances no paper-specific reasoning. Explain unfamiliar or modified constructions. |
| Overloaded noun phrases (E5) | “Our deterministic unconditional working-risk oracle.” | Define it in sentences: the oracle knows the population law, chooses the allocation and weight before seeing samples, and minimizes working risk averaged over them. Then use a short name. |
| Generic wrap-ups (E2) | “Together, these results clarify when synthetic data can help and what is required to turn oracle gains into practical inference.” | Delete it if the findings are already stated. Keep a closing sentence only if it adds a specific supported inference. |
| Editor instructions (E7) | “The synthetic weight is 1−α, so the bias correction must use that weight.” | Present the correct estimator and explain why the weighting matters. |
| Scaffolding (E3) | Repeated “Importantly,” “It is worth noting,” “This highlights,” and triads restating the paragraph. | Delete the phrase or state the substantive connection. Keep useful signposting and real parallel structure. |

## What to preserve

The pass removes avoidable narration, never necessary precision. Keep:

- formal theorem statements, quantifiers, assumptions, inequalities, notation, and
  proof structure;
- claim strength, comparisons, numbers, uncertainty, attribution, and citation scope;
- genuine distinctions such as bias versus MSE, population versus sample quantities,
  and allocation risk versus final-estimator risk;
- material limitations, failed experiments, missing-data disclosures, and external
  resource costs;
- reproducibility information, and required funding, conflict, AI-use, and other
  disclosures;
- venue-supplied checklist questions, guidelines, and template text, which are not
  edit targets even when an author's answer beneath them is;
- effective prose, useful technical repetition, and explanations the audience needs.

A necessary negation stays: “The theorem does not establish finite-sample coverage”
prevents a false inference. An exact commit can belong in a replication manifest.
What matters is the sentence's role and its placement.

Do not ban “not,” hedges, the passive voice, em dashes, technical terms, or lists.
Do not add colloquialisms, deliberate imperfections, synonym churn, or a manufactured
personal voice.

## Relocation and labels

Relocate only to a destination that exists or that the author has authorized, such
as a reproducibility appendix, a README, or a code comment. Do not delete
reproducibility details because they are awkward in prose. Do not claim that a
supplement contains material you have not verified there.

Before replacing a code identifier with a display label, verify the mapping from
the code, the figure source, or the author. If a plot or table is generated with raw
labels and its source is outside the authorized edit, flag the source change rather
than relabeling the output by hand or changing the method.

## Requests to remove AI-like writing

Apply the same checks while drafting, not only when asked to revise.

- **Scope.** Respect a selected passage or a surgical edit. A local polish does
  not trigger a whole-paper rewrite. Within scope, check captions, table notes,
  author-written checklist answers, and appendices.
- **Audit.** For a requested audit, return each finding with its exact passage or
  location, the reader's problem, and a concrete edit (R1). Report a passage that
  already works as passing.
- **Rewrite.** For a requested rewrite, deliver the revised prose. Do not append an
  unrequested account of the editing.
