# Editing and revision

## Match the authorized depth

Read the passage before deciding that it needs a rewrite. For a file edit, identify
the actual file and requested span; do not infer a filename from the first word of
the user's request. Read enough surrounding context to resolve references and
scientific scope. If several files are plausible, resolve the ambiguity before
editing. A user's selection is the edit boundary, not the read boundary. A passage
supplied as a model for revising other material is a reference, not automatically
an edit target. Learn from its logic without silently rewriting it.

Copyediting corrects mechanics and unambiguous local problems. Line editing can
recast sentences and improve paragraph continuity. Structural revision can move
and reshape the requested argument. Drafting supplies new prose from evidence.
An unspecified “polish” authorizes restrained editing, not structural revision.

Keep untouched portions byte-identical for a surgical file edit. Do not normalize
unrelated whitespace, citation commands, notation, or line endings. Preserve the
author's effective sentences. If an out-of-scope problem still materially affects
the accuracy or interpretation of the requested prose, identify it briefly without
performing the larger revision.

## Diagnose before polishing

For substantial revision, diagnose the argument at the scale where it fails:

- **Paper or section:** What should the audience understand or conclude, and which
  evidence earns that takeaway? Give results prominence according to their role in
  the contribution, not their technical complexity or usefulness in answering a
  possible objection. Distinguish explaining a phenomenon, validating a method,
  and establishing its empirical relevance.
- **Paragraph:** What question does this answer, and what does the reader need to
  know first? Does it present the problem before the procedure, and report what
  the evidence established? Develop the evidence and interpretation that the
  takeaway actually requires.
- **Sentence:** Can the same reasoning be expressed more directly? Does each
  connective state the actual relationship between the propositions? What does
  each detail add, and does it belong here, or is it already implied or explained
  nearby?

These questions guide the diagnosis. They are not a template every paragraph must
fit. The [review](review.md) then checks the result: its Pass 1 reverse outline
shows whether the revised passage still gives readers a connected path (A1–A6).
For a substantial revision, that check has four steps: recover the intended
takeaway and its evidence, read the surrounding context, revise within scope, and
check that the resulting passage connects to what precedes and follows it. Return
to the argument if sentence editing exposes a missing premise. Supply a connection
only when the sources support it. Otherwise flag the gap when it is material to the
requested argument. Distinguish an exposition problem from an unresolved scientific
question.

Check the evidence thoroughly, but do not write the check into the manuscript.
Audit logs, implementation correspondence, repair history, and responses to
imagined objections help the revision; they do not belong in the exposition (U5).
When a request is to remove AI-like or machine-sounding prose, read
[Natural prose](natural-prose.md).

Compare the revision's takeaway with the source, not only its wording. Check for
lost conditions, changed comparisons, unsupported certainty, weakened findings, and
added caveats that make the argument less direct without improving its accuracy.
An edit can retain every number yet change the argument by moving the evidence,
replacing the motivation, or introducing a concession. Recheck author-corrected
passages for those errors before polishing them again.

Within the requested scope, preserve the author's scientifically justified
conviction and positioning. Replace vague statements of potential usefulness with
the supported contribution when the sources establish it. Narrow an unsupported
claim locally; do not shrink the research question or weaken unaffected findings.
Retain qualifications that change interpretation and remove those that merely
repeat a restriction already clear to the reader.

## Reviewer feedback

Map the supplied comments to passages and requested actions. For a large revision,
keep a compact working map of addressed, unresolved, and unsupported requests.
Use it to complete the authorized work; do not require a separate approval of the
map when the user has already authorized those changes.

Do not treat a reviewer's assertion as established evidence. If a requested change
requires new analysis, identify that requirement and revise only what the existing
evidence supports. Resolve the specific objection while retaining the supported
core argument; do not turn the manuscript into a running rebuttal or introduce
unspecified reviewer concerns. Keep rebuttal prose separate from manuscript prose.
Describe completed changes accurately, with locations when available; never claim
an experiment or revision was performed when it was only proposed.

## Delivery

For review-only requests, give findings with their exact location, the reader's
problem, and a concrete edit, without changing source files (R1, R2). For edits,
deliver the revised prose or files and any requested response. Describe substantive
changes as such rather than calling them grammatical cleanup, and a changed table
structure as a substantive edit. When an updated rendered artifact is part of
delivery, verify the actual delivered or viewed file against the revised source,
including its displays (D5). A successful temporary build does not establish that
the user's copy is current. Which copies a project keeps, and where, is project
configuration.

Apply the core delivery rule (U6). Do not add an author note repeating a limitation
or requirement already explained in the requested prose or reviewer response. Do
not append generic praise, a repeated summary, or `% REVISED`/`% POLISHED` comments
unless requested.
