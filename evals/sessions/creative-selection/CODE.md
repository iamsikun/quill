# Code notes

Method identifiers used by the simulation scripts:

- `naive_max`: the uncorrected estimate of the top-ranked creative (reported maximum).
- `split_shrink_v2`: split-sample shrinkage with the estimated weight $\hat\lambda$.

In Table 1, "Bias" is the mean signed error of the top creative's estimate across
traffic splits (against the re-measured lift for held-out traffic and the true lift
in simulation), and "MAE" is the mean absolute error across splits. "Campaigns
(sig/total)" counts campaigns whose corrected lift differs significantly from the
reported lift, out of the 40 campaigns evaluated.
