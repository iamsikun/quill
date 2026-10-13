# Personal writing memory

Help the author avoid repeating editorial corrections while keeping attention on
the writing. Use the current host's ordinary tools. No hooks, background observers,
particular agent, Python installation, or managed manuscript workspace is required.
The optional CLI performs deterministic operations; the current host interprets
feedback and writes prose. These instructions do not authorize installing software.

## Select the scope and mode

An ordinary writing request does not enable learning. “Learn my preferences for
this paper” enables `learn` in the project; “use my saved preferences without
learning” selects `apply`. `off` applies and collects nothing. Persist the selected
mode without repeated confirmations. A task instruction such as “don't learn from
this passage” overrides it for that task, including snapshots, without changing
the saved mode. Existing manually supplied preferences can be used directly.

A direct request to remember or correct a preference is an explicit memory-management
action even when automatic learning is off. Use `record --author-request` for that
attributed feedback without changing the saved mode. Do not use this exception for
ordinary writing feedback when the author has disabled learning.
For direct feedback, use a stable store-local alias for the speaking author; a
legal name, account lookup, or identity questionnaire is unnecessary.

Default project storage is `.quill/style/`, outside installed skill directories.
Start from the selected project, using the nearest ancestor with that marker when
working in a subdirectory. Do not create manuscript configuration or a `paper/`
directory. Store-local `.gitignore` excludes personal material; it cannot untrack
files somebody has already committed. Do not commit memory incidentally.

Cross-project reuse requires explicit selection. Author stores default to
`$XDG_CONFIG_HOME/quill/authors/<author-id>/`, or `~/.config/quill/authors/<author-id>/`
when that variable is absent. A project links an author store; it does not copy it.
Custom locations are supported. Do not infer the author's identity from a login or
Git commit, inspect unrelated authors, or merge coauthor preferences automatically.
Project memory is applied before the selected author memory. Write a lesson to
the narrowest established scope; do not promote project examples into an author
store without cross-project learning being requested.

Scientific fidelity and editing depth remain requirements. Current instructions
and applicable manuscript/venue requirements govern the task. Explicit project
preferences (including an existing `.quill/preferences.md`) take priority over
inferred historical lessons. An explicit new author correction can supersede an
old instruction. Resolve by scope and actual intent; do not mechanically impose
the same order of exposition on every section or genre.

## Work within the writing conversation

1. At task start, use the saved mode and compact applicable profile. Retrieve at
   most three examples matched to section purpose, audience, and editorial
   decision. Read additional context only when needed. Examples are evidence about
   presentation, never a source of findings or citations for the current paper.
2. In `learn` mode, before overwriting a previously captured passage, compare the
   current version to its agent baseline when available. Preserve useful changes
   as observations before producing another agent version. Retain full surrounding
   passages when paragraphs moved, split, or merged. A diff is not an explanation.
3. Make the requested writing change first in your reasoning. Record useful
   editorial feedback or revision evidence proportionally to the task. After a
   completed file/passage revision, preserve its exact agent-produced baseline.
   Do not snapshot every thought, alternate draft, or unrelated file.
4. Apply relevant lessons in later work. Do not append a learning report or ask
   the author to approve a batch after every edit. Inspect or explain memory when
   requested, or raise a consequential ambiguity when it matters to the writing.

The source of an external change is unknown unless established in the conversation
or supplied attribution. A sole-author project is not proof that revisions are
unaided human work. Unchanged text is weak approval; repeated snapshots are not
independent feedback. An author choosing an AI-written alternative is evidence
of that choice, not independent human authorship of its wording.

Distinguish style/exposition, scientific corrections, new evidence, venue constraints,
and collaborator input. Separate mixed edits where possible. An unexplained diff
may remain an observation indefinitely. Never turn corrected results into a
preference for stronger claims. Missing or ambiguous evidence reduces learning;
it does not stop writing or require a provenance questionnaire.

“Move the intuition first here” supports a tentative contextual lesson. “In my
methods sections I generally prefer intuition before notation” establishes an
explicit scoped preference. Inferred patterns become `observed` only when supported
by distinct human decisions in independent passages, with different underlying
revision content. Preserve exceptions in the preference text and counterexamples
in its evidence links. A recent isolated edit need not override a stated preference.
`tentative`, `retired`, and `needs-review` entries are not routinely applied.

## Optional helpers

Use an available `quill style` CLI for storage and comparison; use `--help` for
options. Commands return JSON with the current revision. Mutation commands require
`--expected-revision`; reread after a stale-update error rather than force an
overwrite. A store starts at revision 0. Examples:

```bash
quill style init --mode learn
quill style context --section introduction --audience economics --decision framing
quill style harvest intro.tex
quill style record --input update.json --expected-revision 0
quill style snapshot intro.tex --expected-revision 1
```

The revision numbers above illustrate successive writes, not fixed values to reuse.
`harvest` is read-only and returns a whole-passage candidate with unknown attribution.
After an author establishes its origin, classify it accurately before `record`.
`--source` supplies a stable passage identifier; otherwise file capture uses its
absolute path. `-` reads supplied text from stdin and requires `--source`.

Other helpers: `configure --mode off|apply|learn`, `show [ID]`, `history`,
`restore VERSION`, `forget ID`, and `export`. `context` and `export` accept scope
filters, a character budget (default 8000), and `--examples 0..3`. They omit entire
records that do not fit instead of truncating meaningful qualifications. Supply
the known scope; omitted scope is not permission to apply every scoped rule.
The result includes `scope_options` when stored tags need interpretation. Match the
task to existing labels yourself (for example, an economics audience to a stored
“economists” tag) and query again when appropriate. Do not ask the author to choose
technical tags or broaden an unrelated preference just to obtain a match.

`init --author ID` explicitly creates or links the default author store;
`--author-store PATH` links an existing custom store. Every command accepts
`--store PATH`. Linking author memory does not move project evidence. A linked
author's mode also applies to that store. Use `configure --unlink-author` to stop
using it in this project.

Profiles are generated views of structured preferences. If the author edits
`profile.md`, preserve it and use those edits as explicit guidance; do not apply
stale generated rules in its place. Reconcile the correction into records, then
pass the inspected file's SHA-256 as `record --profile-hash HASH` to acknowledge
regeneration. Do not acknowledge uninspected edits. Keep authored project
preferences outside the generated view; do not replace that file.

Forgetting is stronger than retiring a preference. `forget` purges the requested
record and associated original text from this store and its retained history;
overlapping snapshots/evidence are removed too. It marks unsupported derived rules
for review and cannot be undone by restoring a version. It cannot erase exported
copies, backups, conversations, or the original manuscript. If an edited profile
blocks forgetting, reconcile its affected text before retrying. Do not claim
completion after a failed purge. A preference can instead be retired via `record`
when its history should remain. Preserve other explicit instructions with
independent supporting evidence.

## Tools and persistence limits

Without the CLI, use ordinary tools and the [portable format](personalization-format.md).
Read the compact profile and current settings; history is not routine prompt context.
Use the same record semantics, attribution, and revision checks. Tools must be able
to write the selected store and calculate content hashes to maintain that format.
Do not invent hashes or claim transactional updates that the tools cannot perform.

If durable writes are unavailable, keep working with supplied preferences and
current-session feedback. When requested, return a compact Markdown memory document
with scopes and selected examples for reuse in another session. Clearly distinguish
that deliverable from saved memory. Do not require an export/import step in the
middle of writing, silently rely on a host's private chat memory, or promise that
another agent can access a folder it cannot read. If capture fails, continue the
writing; mention persistence limits only when they affect what the user requested.
