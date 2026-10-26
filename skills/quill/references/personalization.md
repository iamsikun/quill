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
- `history/`: earlier versions of `profile.md`, saved before Quill reorganizes it.

```markdown
---
mode: learn       # learn: apply and learn; apply: apply only; off: ignore
---
# Writing profile

## General
- Explain the enabling idea before naming the method, unless the method is
  already familiar to the reader. (stated)

## Results
- Report the estimate before interpreting it. (seen 2×, review)
```

A lesson's marker records its evidence and, optionally, its enforcement level
(below). Lessons without a level are applied while writing.

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
   project lessons; then the profile. The review checks the applicable lessons
   against the finished text (U7).
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

Classify each correction before learning from it, and log the class:

| Class | Example | Where it goes |
|---|---|---|
| Author preference | “Avoid semicolons in prose.” | `profile.md` |
| Project decision | This paper's main message, audience, method names, or which subsection is compressed | The project's `profile.md` |
| Scientific correction | A rate is Θ rather than a bound; an assumption does not support a claim | Nowhere as style. Fix the text. |
| Shared writing-quality repair | Text that failed a rule the skill already states, or a general lesson any author would want, such as explaining an apparent contradiction where it appears | `examples.md`, marked `shared candidate` |

A shared candidate is evidence for improving Quill itself, not an author preference.
Keep it out of the profile unless the author states it as their own preference,
and never edit the skill's instructions from it unless the author asks you to work
on Quill. Changes to the shared skill go through separate review and behavioral
evaluation. One correction can contain both a general lesson and a local
application; record both, with their exceptions.

## Compliance failures

When the author corrects text that an existing lesson, or a checklist rule, already
covered, the problem was applying the guidance, not missing it. Log the entry in
`examples.md` as a `compliance failure`, naming the lesson or rule ID. Do not add a
second, reworded copy of the lesson. Raise the lesson's enforcement level instead:

1. **write** (default): applied while drafting.
2. **review**: also checked line by line in the review's Pass 2. Mark it `review`.
3. **lint**: once the pattern is detectable in text, also add a pattern to the
   profile's `checks` header so `quill check` reports candidates:

```markdown
---
mode: learn
checks:
  - pattern: '[a-z]; [a-z]'
    lesson: Avoid semicolons in prose.
---
```

A lint pattern finds candidates for the review to judge, not violations. Choose a
pattern narrow enough that most hits are real.

When asked to organize a discussion or reflect on failed edits, distinguish direct
feedback from your diagnosis. Record the before/after example, the decision it
changes, and the limits of that lesson. Do not convert an edited connective into
a word ban, a removed redundancy into “always shorten,” or a corrected claim into
“always sound more (or less) confident.” Corrections that add useful detail and
others that remove redundant detail may express the same priority. Put transferable reasoning in skill instructions only when updating the
skill is authorized.

Keep the profile short: when it grows past about 40 lessons, merge overlapping
lessons and remove ones the author no longer follows. Before any change that
merges, rewrites, or removes lessons, copy the current file to
`history/profile-YYYY-MM-DD.md` (add a suffix if that name exists). Never delete a
lesson silently: name each removed or merged lesson in the reply's profile line.
Log each change briefly:

```markdown
## 2026-10-13 · demand-paper/intro.tex · exposition
Quill: We introduce the estimator next. It uses repeated measurements.
Author: Repeated measurements separate signal from noise; we use them to build the estimator.
Lesson: explain the enabling idea before naming the method (seen 2×)
```

## Author control

When asked, explain where a lesson came from using the log; change a lesson's
scope, move, or remove it; restore an earlier profile from `history/`; or delete
log entries the author wants forgotten, together with any lesson that rests only on
them. Removing evidence means reconsidering every lesson it supported. A repeated
snapshot of the same revision is not new evidence. The profile is the machine user's; never add a
coauthor's preferences to it. A coauthor's agreed style belongs in that project's
`profile.md`.

If you cannot read or write the profile, apply the feedback within this
conversation. On request, give the author the profile text to save or to paste
into an assistant without file access, and do not claim that it was saved.
