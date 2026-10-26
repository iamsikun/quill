# Section purpose and technical exposition

Use these as questions about the reader's needs, not templates or venue rules.
Project instructions and current submission requirements determine formatting.
Rule IDs refer to the [checklist](checklist.md).

## Abstract and introduction

Lead with the research question and substantive contribution, making their stakes
clear from the supplied context. Avoid a long generic preamble or inflated
significance claims. Use contribution lists only when useful and consistent with
the manuscript. Do not force business motivation onto a paper whose purpose is
different.

An abstract has room for the main contribution, how its parts connect, the result
with a guarantee or decisive evidence, and the evidence's scope (S1). Decide what
readers should remember, then choose detail by that message:

- **Explain how contributions connect.** “Our framework retains the raw order and
  adds position adjustments, bootstrap rank-mass intervals, and common-intersection
  tiers” lists outputs and leaves readers to relate them. Saying what the method
  provides, what readers receive, and which output carries a theoretical guarantee
  takes more words and less effort. Economy is not the fewest words.
- **Keep the main theorem prominent.** When an abstract gives the central rate
  improvement one clause and a secondary impossibility result two sentences, the
  hierarchy is inverted. Move the secondary result to the body. Keep the main
  result accurate in a short form: if the explicit Θ starting rate needs a nonzero
  leading coefficient, “removes the leading N^{-1/2} term in rank-induced bias” is
  as short and correct. Do not restore the whole technical paragraph to fix one
  boundary.
- **Select evidence for the abstract's message.** “Adjustment reduces the
  cross-setting average magnitude of mean split errors by 48–69% at positions 1–5,
  while per-split absolute error changes little” asks readers to track several
  aggregations. If the point is that two complementary validations support the
  correction, say that, and give the magnitudes in the results. Numbers belong in
  an abstract when they carry its main message.

Keep a material restriction with the claim when omitting it would mislead. Prefer
a concise, narrower accurate claim to an accurate claim followed by qualifications.
Do not repeat a restriction as an apology in each paragraph.

## Literature synthesis

Explain the relationship between the supplied literature and the present claim:
different assumptions, estimands, settings, methods, or evidence. Preserve the
scope of cited findings. A citation should support the proposition to which it is
attached. There is no minimum number of recent papers or requirement to vary the
name of a technical concept.

## Methods and mathematical exposition

Introduce the objects and distinctions a reader needs to interpret the method.
Keep assumptions and quantifiers attached to conclusions. Explain the purpose or
implication of an equation when it is not evident from context; avoid automatically
adding “Intuitively” or a fixed number of explanatory sentences after every formula.

Explain an assumption's analytical purpose when that helps the reader interpret
the result. Its purpose is not automatically a concession or an empirical claim
that the assumption holds (A5).

Use familiar mathematical notation when it states a result more clearly than
verbal circumlocution. Preserve the distinction between a bound and an exact rate:
a tighter rate claim still requires the mathematics to support it. Once a
theoretical setup is established, rely on it where unambiguous rather than
repeating every assumption after every conclusion. Keep a condition visible when
a reader might otherwise infer a different result (S2).

Keep established notation stable. Do not silently repair a theorem, change a
quantifier, replace an estimand with its estimate, or turn asymptotic evidence into
a finite-sample guarantee. Flag an apparent mathematical error separately unless
correcting it is part of the task and adequately supported.

## Results and discussion

Specify which outcome, population, setting, baseline, and uncertainty support a
comparison. Keep exceptions with comparative claims. Reduced bias does not imply
reduced mean squared error; non-significance does not establish equivalence.
An observational association does not establish a causal effect.

For numerical differences and ratios, preserve the operation, direction, units,
and denominator. Distinguish percentage-point differences from relative percentage
changes. Distinguish quantities available in practice from ground truth or errors
observable only in simulation. Do not recommend an operational tuning rule that
requires unavailable information.

State the observed comparison directly within its setting, and distinguish it from
any proposed explanation whose mechanism remains uncertain. Interpret what the
evidence establishes without simply repeating tables (A2). “We examine sensitivity”
names an activity. When the results support robustness, state what remains stable
under the examined changes and connect it to the concern the analysis addresses.
When they reveal fragility, report that instead. A broad summary can be accurate
without repeating every tested setting, provided it preserves the result's meaning
and scope. Do not add an unsupported mechanism to make an observed relationship
sound more satisfying.

### Openings and transitions

A section or paragraph that opens with a correct finding can still fail to connect
to the argument (A3). Before revising an opening, recover what the previous unit
established, which question remains, and why this unit answers it. A validation
section after a theory section might open: the theorem guarantees bias removal
asymptotically, which leaves open how large the correction is at realistic sample
sizes; held-out outcomes test this on real data and calibrated simulations test it
where the true means are known. The fix is the relationship between the analyses,
not “Furthermore.” Do not add a backward reference to every sentence.

### Apparent contradictions

When a result seems to contradict an earlier claim, explain the difference where
the reader meets it (A6). For example, after a bias-correction guarantee, a slightly
higher mean absolute error needs one sentence: the guarantee concerns expected
signed bias, which does not determine mean absolute error in a finite sample.
Name the different target, guarantee, regime, or uncertainty only when the sources
support it. Do not assert a measured variance increase the evidence does not
report. If the discrepancy is unresolved, say so rather than hiding the result.

## Conclusions and supporting detail

Conclude with the main findings, what they change in the reader's understanding,
and supported implications for research or practice. Do not reopen minor technical
extensions or assemble responses to anticipated objections. Include a qualification
when it materially changes the central takeaway, not merely because it exists (S4).

Place detail according to what the reader needs at that point. The main text must
supply the argument and information necessary to interpret its claims. A short
footnote can explain a local convention without interrupting that argument.
An appendix can develop proofs, extensions, implementation, and additional evidence.
Do not move a consequential assumption or adverse finding out of sight merely to
make the main text smoother.

When appendix reorganization is requested, group material by the questions readers
will bring to it. Keep statements near their proofs and related evidence together,
make dependencies clear, and use descriptive headings and accurate pointers from
the main text. Moving a section is incomplete if fragments, duplicate explanations,
or broken references leave its argument scattered. Choose the structure for the
paper rather than imposing a universal appendix order.

## Headings, displays, and notes

Headings, display titles, notes, and body text have different jobs (D1). A section
heading orients the reader. A display's short title or lead identifies its result or
purpose. The note or legend makes the display interpretable on its own: it defines
abbreviations, the sign of a difference, units, aggregation, uncertainty summaries,
and sample restrictions. The body develops what the display implies. A summary or
subtitle should carry the main message, not gloss the topic. Exact formats, such as
noun-phrase or sentence titles, follow the author, genre, and venue.

Captions describe the display, not its editing history (D4). Keep real exclusions,
censoring, and clipping.

### Tables

Make a table readable from its structure, not only from a dense note (D2):

- Name the measured quantity and the comparison.
- Put a shared quantity in a grouped header above its methods or conditions:
  “Mean absolute error” over “Before” and “After,” rather than an “Adjusted” column
  under each of several metrics, or “Residuals after correction” over the method
  names instead of “residual” repeated in each heading.
- Give distinct counts their own named columns instead of slash-packed cells.
- Keep definitions precise: absolute mean error is not mean absolute error, and a
  correction is not a corrected score.

After restructuring, check that every value still sits under its heading (D3).
In rendered output, check that values align under their headings (D5). Compact
comparisons often read best centered under parallel headings, and long numeric
columns decimal-aligned. Keep prose columns left-aligned. Use equal column widths
where parallel conditions are compared. Float placement and a display's design
are the author's and venue's decisions.

### Snapshot provenance

When results depend on a benchmark, leaderboard, or dataset that changes over time,
identify the source, version, and date (D6). Distinguish a release or revision date
from a retrieval date, and verify these facts rather than inferring them from
filenames or timestamps. Where the manuscript records them is its own choice.

Preserve labels and existing LaTeX conventions during prose edits. Do not change
float placement, bibliography style, or notation systems as a side effect of
copyediting.
