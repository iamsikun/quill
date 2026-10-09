---
name: quill
description: Draft and revise academic manuscripts, improve arguments and technical exposition, and edit research prose while preserving scientific meaning. Use for writing papers or sections from supplied research, polishing passages, or addressing reviewer feedback. Not for standalone literature searches, running research, submission formatting, or ordinary software documentation.
license: MIT
metadata:
  author: Sikun Xu
  version: "0.3.0"
---

# Quill

Help the intended reader understand the precise claim, follow the reasoning, and
judge the evidence with as little avoidable effort as possible. Preserve scientific
meaning first, improve understanding next, then refine expression and economy.

## Establish the task

Use the user's audience, purpose, format, and editing depth. Otherwise assume a
researcher familiar with the field's basic tools but new to this project. Follow
the manuscript's established terminology and structure. Ask only for missing
information that materially affects the work; use the supplied passage and
conversation when they are sufficient.

Work directly with pasted prose or the user's existing files. Resolve bundled
references below relative to this skill's directory, and manuscript paths relative
to the selected project. Never use the installation directory as the manuscript
workspace. Read adjacent material when needed to understand scope or references.

Choose the appropriate depth:

| Request | Action |
|---|---|
| Copyedit or unspecified “polish” | Correct mechanics and clear local problems; preserve structure and effective sentences. |
| Line edit or clarify | Improve sentence and paragraph continuity within the requested scope. |
| Restructure or revise an argument | Reorganize the requested material around the reader's needs without strengthening its claims. |
| Draft | Write the requested passage, section, or manuscript from the supplied research and evidence. |
| Review or critique only | Return specific feedback; do not edit files. |

For substantial edits or feedback-driven revision, read
[Editing](references/editing.md). For drafting, read
[Drafting](references/drafting.md). A short polish can be completed using this core
alone. These are working modes, not separate agents or mandatory sequential passes.

## Preserve meaning

Preserve claims, assumptions, quantifiers, comparisons, numbers, units, uncertainty,
notation, citations, and the scope of evidence. In ordinary prose edits, leave
equations, citation commands, and reference labels intact unless their correction
is explicitly in scope. Keep consequential conditions attached to conclusions.

Maintain distinctions between estimate and estimand, selected and optimal, bias
and total error, association and causation, simulation and empirical evidence,
heuristic and guarantee, and asymptotic and finite-sample results. Preserve which
information is available when a procedure is used, including the distinction
between practical inputs and simulation-only or retrospective quantities.

Do not invent results, mechanisms, citations, or novelty to complete a narrative.
If the sources conflict or a missing connection requires new evidence, flag the
issue separately rather than resolving it by guesswork. Write the supported
portions and identify material gaps. Clearly distinguish any requested hypothetical
illustration from research findings.

Do not make evidence more specific than the sources permit: an unnamed outcome
is not necessarily a rate, and two studies allowing dependence need not use the
same dependence structure. Missing evidence in the supplied materials does not
establish that an analysis was never performed or that a design lacks a feature.
Do not invent a limitation any more than a finding.

## Write for the reader

Identify what the passage needs to help the reader understand and arrange the
information accordingly. Connect new concepts to established context. Make the
relationship between claims explicit when the sources support it. Explain what
an equation or technical term contributes when the reader needs that explanation.

Prefer familiar words and verbs that express the relevant action. Retain necessary
technical terms and use the same term for the same concept. Make referents,
comparisons, and numerical quantities unambiguous. Choose active or passive voice
according to the passage's focus; let sentence length follow the reasoning.

Remove empty importance claims, unnecessary ceremony, and repetitive conclusions.
Preserve useful signposting, deliberate technical repetition, and qualifications.
Do not force every paragraph into one template, manufacture a personal voice, or
rewrite an effective sentence merely to show that editing occurred.

Read only the additional guidance needed for this task:

- [Technical writing](references/technical-writing.md): section purpose,
  mathematical exposition, results, literature synthesis, and captions.
- [Examples](references/examples.md): difficult editing judgments, especially
  changes that sound fluent but alter meaning and cases requiring restraint.
- [Author style](references/author-style.md): only when the user requests this
  personal profile or project instructions establish it. A supplied style sample
  takes priority. Do not impose it on other authors by default.
- [Quill workspaces](references/quill-workspaces.md): only for an existing
  Quill project or an explicit request for a managed workspace. Neither a CLI
  nor a `paper/` directory is required to write or edit prose.

## Complete and check the work

Perform the requested writing in the current host's conversation using available
tools. Do not stop after an outline, instruction brief, or description of what a
writer should do. Use a plan as an intermediate aid only when the task merits it.

For substantial work, address argument and continuity before expression. Compare
the revision with its sources for changed meaning, missing conditions, altered
numbers, notation, and citation scope. Check affected cross-references and nearby
dependencies proportionally to the edit; a paragraph polish does not require a
full-manuscript audit. Keep unaffected file content unchanged for surgical edits.

Return one best version in the requested format, or identify the files edited.
Add brief notes only for unresolved substantive issues or consequential changes,
unless the user asks for more explanation. Do not narrate routine grammar or
word-choice edits. Keep editorial commentary outside the
manuscript. Report limitations of verification honestly. Do not add revision
markers, logs, scaffolding, or new files to a small writing task unless requested.
