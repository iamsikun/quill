# Personal writing memory

Help the author avoid repeating editorial corrections. Memory records scoped writing
preferences with the evidence behind them; it does not retrain a model. The current
host interprets feedback and writes the prose. The optional `quill style` CLI does
the deterministic storage and comparison work. Do not install software to use memory.

## Modes and scope

Memory is `off` until the author enables it. “Learn my writing preferences for this
project” selects `learn`, which applies preferences and records evidence. “Use my
saved preferences” selects `apply`, which only applies them. Save the mode once and
follow it in later sessions. An instruction such as “don't learn from this passage”
suspends recording for that task without changing the saved mode. A direct request
to remember, correct, or forget a preference is memory management: carry it out
in any mode (`record --author-request`).

Project memory lives in `.quill/style/` at the project root and is ignored by Git.
An author store (`~/.config/quill/authors/<author-id>/` by default) is used only
when the author links it; linking does not copy anything. Use a short store-local
alias for the author, not a login or commit name. Record lessons in the narrowest
scope that fits. Move a project preference into the author store only when asked
(`promote`). Keep coauthors' preferences separate; a shared profile is an author
store the coauthors explicitly agree to use.

Scientific fidelity and the requested editing depth come first. Then current
instructions and venue requirements, then explicit project preferences (including
`.quill/preferences.md`), then the project memory, then the author memory. A new
explicit correction supersedes an older preference.

## During a writing task

1. Load applicable memory: `quill style context --section S --audience A --decision D`.
   Supply the scopes you know. If `scope_options` lists a stored tag that means the
   same thing (for example `economists` for `economics`), query again with it.
   Examples show writing decisions; they are never evidence for the current paper.
2. In `learn` mode, before overwriting a file you wrote earlier, run
   `quill style harvest FILE`. It compares the file with your last snapshot and
   returns one candidate per edited paragraph (splits and merges stay together).
3. Do the writing.
4. In `learn` mode, after finishing a file or passage, run
   `quill style snapshot FILE --expected-revision N` so later edits can be compared.
   Snapshot finished work, not alternate drafts.

Do not append learning reports or ask the author to approve lessons after each edit.
Explain memory when asked.

## Interpreting revisions

The person who edited a file is unknown unless the author has said so. When harvest
reports `attribution_needed`, ask once: “Are the edits to these files between my
writes yours?” If yes, run `configure --revision-author ID`; if no, run
`configure --no-revision-author`. Either answer is saved, so do not ask again in
that project. Declared candidates arrive as human revisions by that author. Treat
edits the author attributes to a coauthor or a tool as such. Text Quill generated,
including an alternative the author chose, is not independent human writing.

Classify each candidate's `purpose` before recording it: `style`, `exposition`,
`scientific`, `evidence`, `venue`, `collaborator`, or `unknown`. Only style and
exposition evidence can support a preference. `touches` lists the numbers,
citations, references, or mathematics that changed; such edits are usually
scientific corrections. Split a mixed edit into separate records where you can.
A `moved` paragraph usually reflects an ordering decision. Leave an edit as
`unknown` when its purpose is unclear; it then stays in the store as an example.

Record the writing decision, not the wording. “Explain the enabling idea before
naming the method” is a lesson; a reused phrase is not. Correcting a result never
teaches a preference for stronger or weaker claims. Unchanged text is weak approval.

Preference status:

- `explicit`: the author stated it as a general preference (“In methods sections I
  prefer intuition before notation”).
- `observed`: at least two human decisions in independent passages show it.
- `tentative`: a single local edit or one-off instruction (“move the intuition first
  here”). Not applied routinely.
- `retired` or `needs-review`: not applied.

Put exceptions in the preference text and link counterexamples. A single recent edit
does not override a stated preference. Changing an explicit preference requires new
explicit feedback from the author.

## Maintaining memory

`record --input update.json --expected-revision N` saves evidence and preferences
in the [record format](personalization-format.md). Every write needs the current
revision from `show` or `context`. After a stale-revision error, reread the memory
and retry; never force the write.

`profile.md` is generated. If the author edits it, treat the edits as explicit
guidance and do not apply the stale generated rules. Reconcile the edits into
records, then pass `--profile-hash` with the edited file's SHA-256.

Retire a preference with `record` to keep its history. `forget ID` removes the record
and its original text from the store, its history, and any snapshot that contains
the text. Rules that lose their support move to `needs-review`. Forgetting cannot
be undone by `restore`, and it does not reach exported copies, backups, or the
manuscript. `restore VERSION` returns the preferences to an earlier revision and
keeps the evidence, mode, and author link.

When `context` warns that a store has many active preferences, propose merging
overlapping rules or retiring outdated ones. A short profile is applied more reliably.

## Without the CLI or durable storage

Without the CLI, follow the [record format](personalization-format.md) with
ordinary file tools: read `state.json` and `profile.md`, and write records with
the same rules. Only maintain the store if your tools can compute SHA-256 hashes
and replace files atomically. If you cannot write durably, use the preferences
supplied in the conversation. On request, return a short Markdown summary of
them with scopes and examples for reuse in another session. Say that this summary
is not saved memory, and never claim that memory persists when it does not.
