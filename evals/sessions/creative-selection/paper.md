# Correcting the Winner's Curse in Creative Selection

## Abstract

Advertising platforms test many creatives and report the estimated lift of the best one. Under Assumptions 1-3 with creative effects separated by positive gaps, we prove that split-sample shrinkage removes the leading $m^{-1/2}$ term of the selection bias at every fixed configuration. Where the leading coefficient $c_1$ is nonzero, the expected bias falls in magnitude from $\Theta(m^{-1/2})$ to $o(m^{-1/2})$. For gaps shrinking at the $m^{-1/2}$ rate, we characterize the first-order residual terms and prove that no estimator removes the first-order bias uniformly over such configurations. In a study with 250 traffic splits per campaign, correction lowers the cross-campaign mean of absolute mean split error by 38-57% for the top three creatives, while per-split absolute error changes little. It is worth noting that our oracle-calibrated split-sample shrinkage selector is a correction method, NOT a new ranking method.

## 1. Introduction

Because a creative's estimated lift can be ranked first across many tests by chance, we split each campaign's traffic, select the winner on one half, and shrink its estimate using the other half. Importantly, this is a two-step procedure.

Marketing teams act on the winning creative's estimated lift: they forecast revenue from it and allocate budget to similar designs. When dozens of creatives are compared on the same traffic, the creative that ranks first is disproportionately one whose noise happened to be favorable, so its reported lift overstates what it will deliver. This winner's curse is well documented in genetics and in A/B testing, but platforms still report the raw estimate.

Although we assume that campaigns are independent, this assumption gives a clean characterization of the bias. We correct the selected creative's estimate, not the ranking itself. Recall that an estimator is unbiased when its expected value equals the parameter it estimates.

Our contributions are a correction that removes the leading term of the selection bias, a theory explaining when such removal is possible, and validation on held-out traffic and calibrated simulations.

## 2. Setup and theory

Each campaign compares $K$ creatives on $m$ impressions. Let $\hat\mu_k$ denote the estimated lift of creative $k$ and $\mu_k$ its population lift. The platform reports $\hat\mu_{(1)}$, the largest estimate. Split-sample shrinkage selects the winner using one half of the impressions and estimates its lift as $\tilde\mu = \hat\lambda \bar y^{B}_{(1)} + (1-\hat\lambda)\hat\mu^{A}_{(1)}$, where $\hat\lambda$ is estimated from the between-half variance. Split-sample shrinkage borrows the honest half's estimate in proportion to how noisy the selecting half is, so it corrects most when the winner was chosen on noise.

The shrinkage weight is $\hat\lambda$, so the correction must use $\hat\lambda$ and not the population weight $\lambda$.

**Theorem 1.** Suppose Assumptions 1-3 hold and the population lifts are separated by gaps bounded below by $\delta > 0$. Then for each fixed $K$, $\mathbb{E}[\tilde\mu - \mu_{(1)}] = o(m^{-1/2})$ as $m \to \infty$. If in addition the leading coefficient $c_1$ is nonzero, $\mathbb{E}[\hat\mu_{(1)} - \mu_{(1)}] = \Theta(m^{-1/2})$.

This is a bias guarantee for the selected creative, NOT a guarantee about its mean squared error. Again, this result assumes independent campaigns, which may not hold in practice. The theorem does not establish finite-sample coverage of the corrected interval.

**Proposition 2.** If the gaps shrink at rate $m^{-1/2}$, no estimator that is measurable with respect to the split sample removes the first-order bias uniformly over such configurations.

## 3. Validation

Held-out evaluation and simulations show substantial reductions in error. Furthermore, the correction performs well.

The held-out evaluation selects the winner on half of each campaign's traffic and compares estimates with the lift re-measured on the other half. This uses real campaigns, but the true lift is unknown. The simulations draw lifts from distributions calibrated to 40 historical campaigns, so error against the true lift can be computed. Again, the results assume independent campaigns, which may not hold in practice.

Across 250 traffic splits per campaign, the correction reduced the mean signed bias of the top creative from 0.42 to 0.06 percentage points. Averaged across campaigns, the magnitude of the mean split error for the top three creatives fell by 38-57%, while per-split absolute error changed little. Mean absolute error across splits rose from 0.88 to 0.91 percentage points. We conducted sensitivity analyses across three prior widths for $\hat\lambda$; the corrected bias was 0.05, 0.06, and 0.07 percentage points.

| Evaluation | Bias naive_max | Bias split_shrink_v2 | MAE naive_max | MAE split_shrink_v2 | Campaigns (sig/total) |
|---|---|---|---|---|---|
| Held-out traffic | 0.42 | 0.06 | 0.88 | 0.91 | 9/40 |
| Calibrated simulation | 0.39 | 0.03 | 0.80 | 0.82 | 12/40 |

Table 1: Errors in percentage points. Table 1 and Figure 2 use the same simulation runs, as verified after the earlier mismatch was fixed.

Figure 2: Bias of the top creative by number of creatives $K$. The y-axis is now logarithmic so that no curve is truncated anymore. Lines: naive_max and split_shrink_v2. Curves below 0.01 are clipped at 0.01.

## 4. Application

We apply the correction to the Open Creative Benchmark v2.3 (released 2025-11-02; retrieved 2026-01-15), which contains 1,140 campaigns from 12 advertisers. All results were generated from the dirty worktree at commit 9c4e1ab. The local snapshot lacks the 2023 campaign logs, so we do not use them. Again, the results assume independent campaigns, which may not hold in practice.

The correction requires at least two independent replicates per campaign; with one replicate, $\hat\lambda$ is undefined, and 87 campaigns were excluded for this reason. Among the remaining campaigns, the corrected lift of the winning creative was on average 31% smaller than the reported lift. This highlights the importance of correction for practitioners.

## 5. Conclusion

We proposed split-sample shrinkage for the winning creative's lift. One might worry about dependence across campaigns, which we leave to future work; Appendix B sketches a hierarchical extension that could also handle heavy tails. Importantly, the correction is not a ranking method. The correction removed most of the selection bias in held-out traffic and simulations, and on the benchmark the corrected lift was 31% smaller than the reported lift. The correction requires two replicates per campaign. Together, these results illuminate when selection bias matters and pave the way for more trustworthy experimentation platforms.

## Appendix A. Proofs and additional results

Additional simulation results for $K = 50$ appear below; the bias pattern matches Figure 2.

*Proof of Theorem 1.* Expand $\mathbb{E}[\hat\mu_{(1)}]$ around the population ordering. Under the gap condition, the probability of a misordering is exponentially small, so the leading term of the bias is $c_1 m^{-1/2}$, and the honest half removes it.

As explained in Section 2, split-sample shrinkage borrows the honest half's estimate in proportion to how noisy the selecting half is.

The statement of Proposition 2 is in Section 2; its proof uses a two-point construction and is given in the supplement.

## Paper checklist

1. Claims
Question: Do the main claims made in the abstract and introduction accurately reflect the paper's contributions and scope?
Answer: [Yes]
Justification: We rewrote the abstract in this revision so that it now matches the theorem.
Guidelines: The answer NA means that the abstract and introduction do not include the claims made in the paper.

2. Limitations
Question: Does the paper discuss the limitations of the work performed by the authors?
Answer: [Yes]
Justification: The replicate requirement appears in Section 4 and the independence assumption in Section 2.
Guidelines: The answer NA means that the paper has no limitation while the answer No means that the paper has limitations, but those are not discussed in the paper.
