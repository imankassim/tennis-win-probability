# EXP21 - Logistic regression with player/context features added

- Status: Retained
- Depends on: EXP20
- Date: 2026-09-08

## Hypothesis

Adding player context (recent form, surface record, head-to-head, Elo
rating - `pricing/ml/features.py::compute_match_context_features`) should
meaningfully beat state-only (EXP20), since it's exactly the information
Markov and EXP20 alike are blind to.

## Configuration

Same as EXP20 plus `CONTEXT_FEATURES` (`form_a/b`, `surface_rate_a/b`,
`h2h_rate_a`, `elo_a/b`). Same train/test split.

Feature scaling note: Elo (~1500-2000) and the other features (mostly
0-1 or single-digit) sit on wildly different scales. Unscaled, `lbfgs`
took 123 seconds on the full training set and still failed to converge
(a real `ConvergenceWarning`, not just a slow run). Standardising first
(`StandardScaler` in a pipeline) fixed it: 3.2 seconds, same result to
three decimal places.

## Metrics

| Configuration | Brier score | Log-loss |
|---|---|---|
| Markov (comparator) | 0.1839 | 0.5579 |
| EXP20 (logistic, state only) | 0.1744 | 0.5208 |
| EXP21 (logistic, state + context) | 0.1597 | 0.4796 |

Beats EXP20 by a clear margin (8.4% lower Brier) and Markov by 13.2%
lower Brier / 14.0% lower log-loss - context features roughly double the
improvement state-only learning gave on its own.

## Decision

Retained. The representation comparison against EXP23 (the same feature
set on LightGBM instead) is the more interesting result here - see
EXP23's write-up: a linear model captures almost all of the benefit these
context features offer, which says the state→context→outcome
relationship is largely simple/linear, not that context doesn't matter.
