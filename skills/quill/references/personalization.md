# Personal writing memory

Learn how the author likes to write, so they correct the same things less often.
Learning happens during ordinary writing: never pause the task to ask about memory,
and never require setup, approval, or labels from the author. Memory is a readable
profile the author can edit, not a retrained model.

## Files

The profile belongs to the author, not to one project, so every agent on the machine
uses the same one. It lives in `$XDG_CONFIG_HOME/quill/`, which is
`~/.config/quill/` when that variable is unset:

- `profile.md`: the lessons Quill applies. It is the source of truth; the author may
  edit it directly, and those edits are authoritative.
- `examples.md`: a log of the edits and feedback lessons came from, each entry
  naming its project.

```markdown
---
mode: learn       # learn: apply and learn; apply: apply only; off: ignore
---
# Writing profile

## General
- Explain the enabling idea before naming the method, unless the method is
  already familiar to the reader. (stated)

## Results
- Report the estimate before interpreting it. (seen 2×)
```

A project needs its own `.quill/style/` folder, which Git ignores, only for:

- `baselines/`: Quill's last version of each file it wrote, kept by `quill style`.
- `profile.md` (optional): lessons that apply only to this paper, such as a
  coauthor's agreed style or a venue's conventions, and project settings. Its
  header may set `mode` for this project and `edits: others` when coauthors or
  other tools also edit the files; Quill then learns here only from the author's
  feedback in conversation.

“Learn my writing style” creates the profile with `mode: learn`. Change the mode
when the author asks to pause learning or stop using the profile, in the project
header if the request concerns only this project. A writing request alone never
creates memory.

## During a writing task

None of these steps delays the requested writing.

1. Read the profile, and the project's `profile.md` if one exists. Apply lessons
   that fit the passage's section, audience, and genre. Fidelity to the research
   and the requested editing depth come first; then current instructions; then
   project lessons; then the profile.
2. With `mode: learn`, unless the project sets `edits: others`, run
   `quill style changes FILE` before editing a manuscript file. It shows
   the author's edits since your last version: changed paragraphs, flagged when
   they change numbers, citations, references, or mathematics, or move a
   paragraph. A missing baseline means there are no prior edits to learn from.
   Skip this step if the CLI is unavailable.
3. Do the requested writing.
4. With `mode: learn`, learn from those edits and from this conversation's
   feedback (below). Save new lessons in `profile.md` and log their supporting
   feedback or edits in `examples.md`. Unless the project sets `edits: others`, when the CLI is
   available, run `quill style baseline FILE` for each manuscript file you wrote,
   including its first write. This establishes the baseline for the author's
   next edits even when there was no earlier version to compare.
5. If the profile changed, end the reply with one short line, such as “Added to your
   writing profile: report the estimate before interpreting it.” Ask nothing. If
   the host blocks writing to the profile, keep applying the lesson in this
   conversation and say once that it could not be saved.

## Learning

Learn writing decisions, not wording. “Explain the enabling idea before naming the
method” is a lesson; a favorite phrase is not. Place each lesson under the heading
for where it applies, and include the exceptions the author has shown. Lessons go
in the profile unless they hold only for the current project.

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
## 2026-10-13 · demand-paper/intro.tex · exposition
Quill: We introduce the estimator next. It uses repeated measurements.
Author: Repeated measurements separate signal from noise; we use them to build the estimator.
Lesson: explain the enabling idea before naming the method (seen 2×)
```

## Author control

When asked, explain where a lesson came from using the log; change, move, or remove
lessons; or delete log entries the author wants forgotten, together with any lesson
that rests only on them. The profile is the machine user's; never add a
coauthor's preferences to it. A coauthor's agreed style belongs in that project's
`profile.md`.

If you cannot read or write the profile, apply the feedback within this
conversation. On request, give the author the profile text to save or to paste
into an assistant without file access, and do not claim that it was saved.
