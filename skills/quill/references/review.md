# Review before delivery

Loading guidance does not apply it. Review the finished text against the
[checklist](checklist.md) before delivering it. The review has two passes with
different jobs, and passing it is part of finishing the task.

## Scale

| Request | Procedure |
|---|---|
| Copyedit or local polish | Brief self-check of the universal checks (U) and the profile. No separate pass. |
| Line edit or paragraph revision | Both passes, briefly, in your own context. |
| Section revision | Both passes by an independent reviewer when available, targeted repairs, and the recheck. |
| Draft, restructure, or full manuscript | Task frame and reader path, both passes for each section, and a cross-section Pass 1. |
| Review or audit only | The passes structure the review. Files stay unchanged (R2). |

## Protocol

1. **Frame the task.** Before writing, establish the audience, purpose, authorized
   scope, central takeaway, sources, protected content, and applicable profile
   lessons. For drafting and restructuring, sketch the intended reader path: one
   line per paragraph giving its role and its link to the paragraph before. The
   frame selects the checklist modules through the routing table.
2. **Pass 1: meaning and argument.** Compare the draft with its sources (U1–U3, A7,
   A8). Check that the central contribution stays prominent (A1). Write a reverse
   outline from the draft alone, one sentence per paragraph, and compare it with the
   intended reader path (A2–A6). Where a paragraph's outline sentence does not
   follow from the one before, the reader path is broken there. At manuscript scale,
   also check across sections (A10). This pass checks fidelity to the supplied
   research. It does not prove theorems or verify literature unless asked.
3. **Pass 2: expression and rule coverage.** Check the revised text against every
   check in the routed modules, and revisit the Pass 1 findings. Decide keep, delete,
   rewrite, or relocate for each finding. When the `quill` CLI is available, run
   `quill check FILE` on manuscript files. Its hits are candidates. Judge each one in
   context, and never treat their number as a score.
4. **Repair only flagged spans, then recheck them.** Leave other text byte-identical.
   Recheck each changed span against the sources for claims, conditions, numbers,
   notation, and citations. `quill check FILE --against OLD` reports changed numbers,
   citations, references, mathematics, and edits outside `--lines`. A finding is
   resolved only after this recheck.
5. **Bound the iteration.** A pass is complete when its checks are satisfied, with
   or without edits. After both passes, allow at most one more targeted cycle for
   remaining concrete findings. Then report what stays unresolved.
6. **Finish.** The task is done when the deliverable is complete, scientifically
   accurate, and passes the review. In a project where the CLI is available, run
   `quill review record FILE` for each reviewed manuscript file. Any later edit
   makes that record stale, and `quill review status` reports it.

Keep frames, outlines, check statuses, and findings out of the manuscript and the
reply. A review-only request returns findings (R1); a rewrite returns the prose.

## Independent reviewer

For section-scale and larger work, have a reviewer in a fresh context run each pass
when the host supports subagents. A fresh reader sees what the text says, not what
the writer meant.

- **Give it:** the request and edit boundary, the sources, the current draft, this
  file, the checklist with the routed modules named, and the active profile. Do not
  give it your reasoning or your intended reader path.
- **Ask for:** a status for each routed check (pass, needs repair, not applicable,
  or unable to verify), and for each finding the location, quoted text, problem,
  and proposed action. In Pass 1, the reviewer writes the reverse outline. Compare it
  with your intended reader path: a gap shows what a new reader actually takes away.
- **Adjudicate:** the reviewer may report no findings and has no quota. Check each
  finding against the sources before applying it. Reject a finding that would
  change the science, exceed the edit scope, or rewrite effective prose, and keep
  a one-line reason for each rejection in your working notes.
- **Without subagents:** run the same passes yourself after rereading the file and
  the checklist from disk, not from memory.

## Long sessions

A revision can span many rounds. At the start of each new substantive request in a
long session, and after any context summary, reread the checklist and the profile
from disk rather than relying on what you remember of them.
