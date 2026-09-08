# EXP22 — XGBoost/LightGBM classifier, state features only

- Status: Retained
- Depends on: EXP20
- Date: 2026-09-08

## Hypothesis

Gradient-boosted trees should capture non-linear interactions between
score-state features (e.g. "break point AND deciding set" mattering more
than either alone) that a linear model (EXP20) can't, even from the same
inputs.

## Configuration

`pricing/ml/train.py::train_and_evaluate(..., "lightgbm",
STATE_FEATURES, ...)` — LightGBM (`LGBMClassifier`, `n_estimators=100,
max_depth=6`, otherwise default — untuned, same spirit as EXP13's
shrinkage strength). Same train/test split as EXP20/21.

## Metrics

| Configuration | Brier score | Log-loss |
|---|---|---|
| Markov (comparator) | 0.1839 | 0.5579 |
| EXP20 (logistic, state only) | 0.1744 | 0.5208 |
| EXP22 (LightGBM, state only) | 0.1726 | 0.5141 |

A small edge over EXP20 (1.0% lower Brier) from the same information —
some non-linear structure in the state→outcome relationship, but not a
large amount.

## Decision

Retained, as the tree-based half of the state-only floor EXP23/24 build
on. The state-only representation comparison (EXP20 vs EXP22) shows model
family matters far less here than adding context does (compare the much
larger EXP20→EXP21 jump) — see EXP24's write-up for the full picture.
