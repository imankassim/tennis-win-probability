# 5. Use XGBoost or LightGBM for the learned win-probability model

- Status: Accepted
- Date: 2026-09-08

## Context

The ML problem (charter) is to combine an analytic point-based model with
contextual and momentum signals, on a dataset that is tabular (score state,
rankings, form, surface, momentum features), moderate in size (point-level
records from a bounded set of Grand Slam years), and where feature
importance and explainability matter for the "expose the Markov versus ML
contribution split" governance requirement.

## Decision

Use gradient-boosted trees (XGBoost or LightGBM) as the learned
win-probability model (EXP22–24), after a logistic-regression baseline
(EXP20–21) for comparison.

## Consequences

- Gradient-boosted trees handle tabular, mixed-scale features (score state,
  rank gaps, rolling form) without extensive preprocessing, and expose
  feature importances that support the explainability governance
  requirement.
- A logistic-regression stage (EXP20–21) is retained as a simpler,
  more interpretable comparator before committing to a more complex model,
  consistent with the "baseline first" principle and the negative-result
  policy (a more sophisticated model is not promoted just for being more
  sophisticated).
- Deep learning is explicitly not chosen for the initial ML problem: the
  dataset size and tabular structure do not justify it, and it would work
  against the explainability and auditability requirements.
