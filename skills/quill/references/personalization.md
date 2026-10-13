# Personal writing memory

Learn how the author likes to write, so they correct the same things less often.
Learning happens during ordinary writing: never pause the task to ask about memory,
and never require setup, approval, or labels from the author. Memory is a readable
profile the author can edit, not a retrained model.

## Files

Project memory lives in `.quill/style/` and is ignored by Git:

- `profile.md`: the lessons Quill applies. It is the source of truth; the author may
  edit it directly, and those edits are authoritative.
- `examples.md`: a log of the edits and feedback lessons came from.
- `baselines/`: Quill's last version of each file it wrote, kept by `quill style`.

```markdown
---
mode: learn       # learn: apply and learn; apply: apply only; off: ignore
edits: mine       # mine: edits to Quill's text are the author's; unknown: learn from conversation only
author_profile:   # optional path to a profile shared across the author's projects
---
# Writing profile

## General
- Explain the enabling idea before naming the method, unless the method is
  already familiar to the reader. (stated)

## Results
- Report the estimate before interpreting it. (seen 2×)
```

“Learn my writing style” creates this profile with `mode: learn`. Set `edits:
unknown` if the author mentions that coauthors or other tools also edit the files.
Change the mode when the author asks to pause learning or stop using the profile.
A writing request alone never creates memory. For memory shared across projects,
keep a profile and log in `~/.config/quill/authors/<name>/` and link it with
`author_profile`.

## During a writing task

None of these steps delays the requested writing.

1. Read `profile.md`, and the linked author profile if any. Apply lessons that
   fit the passage's section, audience, and genre. Fidelity to the research and
   the requested editing depth come first; then current instructions; then the
   project profile; then the author profile.
2. With `mode: learn` and `edits: mine`, before editing a file you wrote earlier,
   run `quill style changes FILE` to see the author's edits since your last version.
   It lists changed paragraphs and flags changed numbers, citations, references,
   mathematics, and moved paragraphs. Skip this step if the CLI is unavailable.
3. Do the requested writing.
4. With `mode: learn`, learn from those edits and from this conversation's
   feedback (below). With `edits: mine` and the CLI available, then run
   `quill style baseline FILE` for each file you wrote.
5. If the profile changed, end the reply with one short line, such as “Added to your
   writing profile: report the estimate before interpreting it.” Ask nothing.

## Learning

Learn writing decisions, not wording. “Explain the enabling idea before naming the
method” is a lesson; a favorite phrase is not. Place each lesson under the heading
for where it applies, and include the exceptions the author has shown.

- A general preference the author states (“in methods sections I prefer intuition
  before notation”) enters the profile at once, marked `(stated)`.
- A local instruction (“here”, “in this paragraph”) or a single edit is logged
  only. When the same decision appears in two independent passages, add the
  lesson, marked `(seen 2×)`, and update the count as more evidence appears.
- Corrections of substance teach nothing about style: changed results, numbers,
  citations, notation, new evidence, venue requirements, and a collaborator's
  input. Correcting a claim's strength is not a preference for stronger or weaker
  claims. When an edit mixes substance and style, learn only from the style part.
- Unchanged text is weak evidence of approval. Text Quill wrote, including an
  alternative the author chose, is not the author's writing.
- A newer stated preference replaces an older one; an occasional contrary edit
  becomes an exception or is left in the log.

Keep the profile short: when it grows past about 40 lessons, merge overlapping
lessons and remove ones the author no longer follows. Log each change briefly:

```markdown
## 2026-10-13 · intro.tex · exposition
Quill: We introduce the estimator next. It uses repeated measurements.
Author: Repeated measurements separate signal from noise; we use them to build the estimator.
Lesson: explain the enabling idea before naming the method (seen 2×)
```

## Author control

When asked, explain where a lesson came from using the log; change, move, or remove
lessons; or delete log entries the author wants forgotten, together with any lesson
that rests only on them. Copy lessons to the author profile only on request. Keep
each author's profile separate; use a shared profile only when coauthors ask for one.

If you cannot write files, apply the feedback within this conversation. On request,
give the author the profile text to save, and do not claim that it was saved.
