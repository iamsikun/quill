# Your writing profile

Quill learns how you write from the feedback you give it and the edits you make to
text it wrote. The [README](../README.md#your-writing-profile) shows how an edit
becomes a lesson. This page covers where the profile lives, how to control it, how
it is shared across agents and projects, and how Quill sees your edits. The agent's
instructions are in the [personalization workflow](../skills/quill/references/personalization.md).

## What Quill learns

- A preference you state, such as “in methods sections I prefer intuition before
  notation,” is learned at once.
- A pattern in your edits is learned once it appears in two separate passages.
  A single local edit is only logged.
- Corrections of results, numbers, citations, or notation never become style
  lessons. Correcting a claim's strength is not a preference for stronger or weaker
  claims.
- A decision that holds only for one paper, such as its audience or the name of its
  method, stays with that project.
- If you correct something a lesson already covers, Quill checks that lesson line by
  line in its review from then on. For a pattern that is easy to detect, it can add
  a lint pattern so `quill check` flags it.

Quill never stops the writing to ask about memory, and it tells you in one line when
it adds or changes a lesson.

## Author control

Your profile belongs to you, not to one project. It lives in `~/.config/quill/`
(or `$XDG_CONFIG_HOME/quill/`) as plain Markdown:

- `profile.md`: the lessons, grouped by where they apply. Edit it freely. Your edits win.
- `examples.md`: the feedback and edits each lesson came from.
- `history/`: earlier versions of the profile, saved before Quill reorganizes it.

Ask Quill why a lesson exists, change its scope, forget it, restore an earlier
profile, or pause learning. Removing the evidence for a lesson also removes the
lesson if nothing else supports it. Memory adapts the instructions Quill follows.
It does not retrain a model.

## Every agent, every project

Every agent with Quill installed (Claude Code, Codex, Cursor, Gemini CLI, Copilot,
OpenCode) reads and updates the same profile, in any project. To use it on several
machines, sync that folder as you would other dotfiles.

Because the profile is outside your project, an agent may ask permission the first
time it reads or writes it. To allow it once and for all, add the folder to Claude
Code's `permissions.additionalDirectories` setting, or to Codex's
`[sandbox_workspace_write] writable_roots` in `~/.codex/config.toml` (as an absolute
path).

**ChatGPT Work.** Local tasks can use the profile when file access is permitted.
Cloud tasks can use it only through an online, connected computer with local access
enabled. Otherwise, attach or paste `profile.md`; an attachment supplies a snapshot
and does not save new lessons back to your local file. See OpenAI's
[local file access documentation](https://learn.chatgpt.com/docs/enterprise/chatgpt-work-local-security).

## Project files and coauthors

A project's `.quill/style/` folder, which Git ignores, holds only what belongs to that
project: Quill's last version of each file it wrote, so it can see your edits, and
an optional `profile.md` for lessons that apply only to that paper.

If coauthors also edit a project's files, say so. Quill records `edits: others` there
and learns in that project only from your feedback in conversation. A coauthor's
preferences never enter your personal profile.

## Seeing your edits

Two optional commands help Quill see your edits:

```bash
quill style changes                     # paragraphs you changed since Quill last wrote each file
quill style baseline sections/intro.tex # record Quill's new version after it writes
```

`changes` flags edits that touch numbers, citations, references, or mathematics,
since those are usually corrections rather than style. Without the CLI, Quill still
learns from feedback in conversation.

The [evaluation protocol](../evals/README.md#personalization) describes how the
learning workflow is tested.
