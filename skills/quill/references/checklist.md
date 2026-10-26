# Review checklist

This file holds every rule the review checks. Each rule has an ID, a scope, one
yes/no question, a default action, its exception, and a contrasting example. The
other references explain the reasoning and give longer examples. They cite these
IDs and do not restate the rules.

A **yes** answer passes the check. For a **no**, choose **keep, delete, rewrite, or
relocate** for the span, following the default action. Record each check as
*pass*, *needs repair*, *not applicable*, or *unable to verify*. Keep these records
out of the manuscript and the reply.

## Routing

The universal checks apply to every task. Add the modules for the task and for
each section or display in scope. Do not choose rules by feel.

| Task or content | Modules |
|---|---|
| Copyedit or local polish | U |
| Line edit or paragraph revision | U, A3–A5, E |
| Section revision | U, A, E, and the section's module |
| Draft, restructure, or full manuscript | U, A, E, every section module in scope, D |
| “Remove AI-like writing,” “sounds like ChatGPT,” or a similar request | U, E, A8, A9, D4, and the section modules in scope |
| Abstract or introduction | S1 |
| Methods, theorems, or proofs | S2 |
| Results or discussion | S3 |
| Conclusion or appendix | S4 |
| Tables, figures, captions, notes, or headings | D |
| Rendered output (PDF, HTML, slides) | D5 |
| Review or audit only | The modules above for the content; R |

## U · Universal

**U1 · Meaning.** Do claims, assumptions, quantifiers, comparisons, numbers, units,
uncertainty, notation, citations, and evaluation status match the sources?
Default: restore the source's meaning. Flag a conflict between sources rather than
choosing one. Except: corrections the request authorizes and the sources support.
*Fails:* “consistent as n grows” becomes “accurate in any sample.”

**U2 · Distinctions.** Are estimate and estimand, selected and optimal, bias and total
error, association and causation, simulation and empirical evidence, heuristic and
guarantee, and asymptotic and finite-sample results still distinct?
Default: restore the distinction, even if a word repeats.
*Fails:* replacing “selected” with “best” for variety.

**U3 · Scope.** Does every change lie within the requested span and editing depth?
Default: revert changes outside the span, and report an out-of-scope problem in one
line only if it materially affects the requested text. Untouched file content stays
byte-identical. Reference passages, protected author text, and venue-supplied
template or checklist text stay unchanged unless they are the edit target.
*Fails:* a requested polish of paragraph 3 also rewords paragraph 5 or a
checklist question.

**U4 · Effective prose.** Is every changed sentence better for the reader, not merely
different? Default: restore the original. Except: changes needed by another check.
*Fails:* “We randomly assigned 600 participants to one of three groups” becomes
“A randomized allocation procedure was implemented across a tripartite grouping.”

**U5 · Research, not workflow.** Is the text free of revision history, repair
announcements, verification narration, editor reminders, agent workspace limits,
and revision markers? Default: delete it, or describe the actual method or finding
instead. Relocate exact versions, commands, and hashes only to a real or authorized
reproducibility destination. Except: provenance the reader needs (see D6).
*Fails:* “The profiles use the recorded dirty worktree at commit 3f2a9c1.”
*Fails:* “Complete runtime records are unavailable in this local snapshot.” If
the paper omits them, “Complete execution-time records are not provided” states
the fact without implying the authors lack them.

**U6 · Delivery.** Does the reply give the requested deliverable and nothing
unrequested? Default: remove checklists, editing explanations, praise, and advice.
Add one note only for a material issue that remains unresolved.
*Fails:* a requested rewrite followed by an essay on what was changed and why.

**U7 · Profile.** With an active writing profile, does the text follow every lesson
that fits this passage? Default: apply the lesson. Except: current instructions and
scientific accuracy take precedence.

## A · Meaning and argument

**A1 · Main message.** Can a reader state the passage's intended takeaway, and is the
central result, contribution, or implication as prominent as its role warrants?
Default: put it where the reader meets it first and give it its own sentence. An
elaborate qualification or a secondary result does not displace it merely because
it is technical.
*Fails:* an abstract gives three sentences to a local impossibility result and buries
the rate improvement that is the paper's main theorem.

**A2 · Evidence and its role.** Does each piece of evidence say what it establishes,
and is its role clear: explaining a phenomenon, validating a method, or showing
empirical relevance? Default: state the finding. “We examined X” names an activity.
*Fails:* “We conducted sensitivity checks under four covariance structures” when the
point is that the estimate kept its sign and size under all four.

**A3 · Reader path.** Does each paragraph and section open from what the previous
unit established, the question that remains, and why this unit answers it?
Default: write the connection from the real relationship between the analyses.
Except: a self-evident sequence. A transition word is not a connection.
*Fails:* “Held-out tests and calibrated simulations show substantial reductions in
error” opens a validation section without saying that the theory leaves a
finite-sample question these analyses answer.

**A4 · Problem before procedure.** Where the need for a method or step is not yet
clear, does the text state the problem before the mechanics?
Default: state the problem in one sentence, then the procedure as its response.
Except: familiar operations.
*Fails:* “Because a model can occupy different ranks across resamples, we report
rank intervals” before the reader learns that a small benchmark may not resolve the
ordering.

**A5 · Connectives.** Does each connective express the actual relationship: purpose,
cause, evidence, implication, sequence, contrast, or concession?
Default: correct the relationship, not only the word.
*Fails:* “Although we assume independent tasks, this assumption provides a clean
demonstration” presents a purpose as a concession. “We assume independent tasks
for a clean theoretical demonstration.” This is not a ban on “although.”

**A6 · Apparent contradictions.** When a result appears to conflict with an earlier
claim, is the difference explained where the reader meets it?
Default: name the different target, guarantee, regime, or uncertainty the sources
support. If the sources do not resolve it, say so. Never invent a mechanism or hide
the adverse result.
*Fails:* reporting that mean absolute error rose slightly right after a bias guarantee,
with no sentence explaining that a guarantee on expected signed bias does not bound
mean absolute error. Do not claim a variance increase the evidence does not measure.

**A7 · Earned confidence.** Are supported findings stated directly within their scope,
with no overclaim and no weakened contribution?
Default: “Under Assumptions A–C, we establish X” rather than stacked hedges. Narrow
an unsupported claim locally. Keep the author's supported ambition.
*Fails:* “Our analysis may suggest that X could hold.” *Fails:* “The method also
helps” for a demonstrated main contribution.

**A8 · Limitations.** Is each material limitation stated once, where it affects
interpretation, including in a display that is read on its own?
Default: keep the first necessary statement and delete repetitions. Never delete
the only statement of a consequential limitation, a failed experiment, or a
missing-data disclosure.
*Fails:* the same independence assumption repeated after each result and in each
caption.

**A9 · Detail for the reader.** Does each detail help this reader at this point?
Default: add explanation that resolves a real question, delete bookkeeping already
implied, and move secondary detail to where readers look for it (S1, S4).
Do not reproduce the checking process in the text.
*Fails:* “If q models tie across q rank positions” where “If q models tie” suffices.
*Fails, the other way:* deleting the short note that a reader needs to interpret a
tie-handling convention.

**A10 · Cross-section coherence.** At manuscript scale, does the conclusion answer what
the introduction promised, and do terms, notation, and numbers agree across sections?
Default: repair the section that drifted, within scope, and flag the rest.

## E · Expression

These patterns make careful prose read like an assistant's report. Judge each
instance by its function in context. Delete or relocate as readily as you rewrite,
and never replace a deleted sentence with an equally generic one.

**E1 · Positive statement.** Does the text state what the method or result is, rather
than an alternative the reader was not considering?
Default: state it positively. Except: a contrast that prevents a likely false
inference or marks a real scientific distinction.
*Fails:* “This is an allocation guarantee, NOT a guarantee for the final estimator.”
“The theorem controls the selected allocation's population working risk,” followed by
the conditions under which this extends to the final estimator's MSE if readers need
them. *Keep:* “The theorem does not establish finite-sample coverage” when readers
would otherwise assume it.

**E2 · Empty emphasis and wrap-ups.** Is every importance claim, summary, or closing
sentence specific and supported?
Default: delete it when the findings are already stated. A closing sentence must add
a specific supported inference.
*Fails:* “Together, these results clarify when synthetic data can help and what is
required to turn oracle gains into practical inference.”

**E3 · Scaffolding.** Do “Importantly,” “It is worth noting,” “This highlights,” and
similar phrases, and three-part summaries, carry a connection the sentence needs?
Default: delete the phrase or state the substantive connection. Keep useful
signposting and genuine parallel structure.

**E4 · Audience fit.** Does every explanation serve the intended audience?
Default: delete elementary material that advances no paper-specific reasoning.
Explain unfamiliar or modified constructions.
*Fails:* “A nominal 95% procedure aims for 0.95” in a paper for statisticians.

**E5 · Names.** Are methods and objects called by established, readable names, with
compound descriptions defined in sentences first?
Default: define what the object knows, when it acts, and what it optimizes, then
use a short stable name. Use the community's established names over coined labels.
*Fails:* “Our deterministic unconditional working-risk oracle” on first use.

**E6 · Reader-facing labels.** Are code identifiers kept out of prose, headings,
legends, and tables?
Default: use a display label whose mapping to the code you have verified, such as
“Adaptive plug-in” for `corrected_adaptive_gn`. Keep implementation mappings in
code documentation. Flag a plot whose source must change. Never silently change
a method or its results.

**E7 · Exposition, not instructions.** Does the text present the method rather than
remind an editor how to repair it?
Default: state the correct object and its scientific role.
*Fails:* “The synthetic weight is 1−α, so the bias correction must use that weight.”

**E8 · Hedges.** Does each hedge mark genuine uncertainty about something specific?
Default: replace stacked or habitual hedges with explicit scope (A7).

**E9 · Consistency.** Is the same concept named the same way, and are numbers, units,
and ranks expressed consistently within a comparison?
Default: make them consistent, subject to author and venue conventions.

## S · Sections

**S1 · Abstract and introduction.** Does the abstract give the main contribution, the
result that most earns it, and the evidence's scope, and does the introduction
develop why the question matters and how the evidence answers it?
Default: select numbers and results by the abstract's message and space. Prefer a
concise accurate formulation to an accumulation of qualifications. Keep a
restriction whose omission would mislead.
*Fails:* “adjustment reduces the cross-setting average magnitude of mean split errors
by 48–69% at positions 1–5, while per-split absolute error changes little,” when the
abstract's job is to say that sample splitting and calibrated simulations validate
the correction. The detail belongs in the results.
*Fails, the other way:* “the bootstrap reduces the ranking bias from Θ(N^{-1/2}) to
o(N^{-1/2})” when the Θ starting rate requires a nonzero leading coefficient. “The
bootstrap removes the leading N^{-1/2} term in rank-induced bias” is accurate and
as short.

**S2 · Methods and mathematics.** Are notation, quantifiers, bounds versus exact rates,
and the established assumption context preserved, and is each equation's role clear
where it is not evident?
Default: rely on the established setup instead of repeating every assumption, and
keep a condition visible where readers might infer a different result.

**S3 · Results and discussion.** Does each comparison specify its outcome, population,
setting, baseline, and uncertainty, with operations and denominators preserved?
Default: state the observed comparison, then any proposed explanation at its own
level of support. Call a result robust only when the checks show stability.

**S4 · Conclusion and appendix.** Does the conclusion give the main findings and
their implications, and is supporting material grouped by the questions readers bring?
Default: remove reopened minor extensions and responses to anticipated objections.
Keep limitations that change the takeaway. In appendices, keep statements with
proofs and give accurate pointers.

## D · Displays

**D1 · Distinct jobs.** Does each heading orient, each display's lead identify its
result or purpose, each note or legend make the display interpretable, and the body
develop the implications?
Default: move content to the element whose job it is. Adapt the format to genre and
venue. *Fails:* a section heading that is a vague gloss of its contents.

**D2 · Table structure.** Does the table name the measured quantity and the
comparison, group a shared quantity above its methods or conditions, give distinct
counts separate columns, and define abbreviations, units, aggregation, and reference
quantities?
Default: add a grouped header such as “Mean absolute error” above “Before” and
“After” instead of repeating “Adjusted” under each metric. Split a “3/5” tier-count
cell into named columns. Distinguish absolute mean error from mean absolute error.

**D3 · Values under the right headings.** After a table edit, does every value still
sit under the heading it belongs to?
Default: compare each row with its source. A changed header structure is a
substantive edit.

**D4 · Captions describe the display.** Does each caption or note describe what the
display shows, without announcing repairs or assuring consistency?
Default: “The vertical axes are logarithmic,” not “The logarithmic vertical scale
displays every curve without truncation.” Delete “The curves and Table 4 use the same
results,” or state the table's role. Keep actual exclusions, censoring, or clipping.

**D5 · Rendered artifact.** For rendered output, has the delivered file the user
actually opens been checked: values under their headings, numeric alignment, and the
expected revision present?
Default: rebuild or recheck that file. A successful temporary build does not
establish that the user's copy is current. Use alignment that suits the comparison:
values centered or decimal-aligned under parallel headings, prose left-aligned.

**D6 · Snapshot provenance.** When results depend on a changing source such as a
benchmark or leaderboard snapshot, does the text identify its source, version, and
date, distinguishing release dates from retrieval dates?
Default: state the verified facts. Never infer them from filenames or timestamps.
Placement is the manuscript's choice.

## R · Review-only output

**R1 · Actionable findings.** Does each finding give the exact passage or location,
the reader's problem, and a concrete edit or decision?
Default: quote the span, name the problem, and propose keep, delete, rewrite, or
relocate. Report effective passages as passing; there is no quota of findings.

**R2 · Files unchanged.** Are all files unchanged after a review-only request?
Default: revert any edit.
