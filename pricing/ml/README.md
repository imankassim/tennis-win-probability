# pricing/ml

Feature engineering and the machine-learned win-probability model
(LightGBM) using state and context features.

## Status

Journey 11 (ML probability model) is complete: EXP20-24 evaluated on real
data, EXP24 (LightGBM, state + context + momentum) is the leading
candidate. Not yet wired into the live API — the logical architecture
computes the Markov and ML estimates independently and blends them
(Journey 12), rather than one replacing the other.

## Structure

- `features.py` — `compute_match_context_features()` (recent form,
  surface record, head-to-head, Elo, one archive pass, no-look-ahead) and
  `build_point_features()` (one row per point: state + momentum + the
  match's context features, labelled by outcome).
- `train.py` — `match_level_split()` (chronological, match-level — the
  most recent matches held out, never splitting one match's points across
  train and test) and `train_and_evaluate()` (logistic regression or
  LightGBM over a chosen feature set, scored on the held-out set).

## Real evidence

Evaluated on a chronological 80/20 match-level split of the full archive
(4,363 train matches / 715,055 points, 1,090 test matches / 175,301
points — test-set metrics only, below):

| Configuration | Brier score | Log-loss |
|---|---|---|
| Markov (comparator) | 0.1839 | 0.5579 |
| EXP20 — logistic, state only | 0.1744 | 0.5208 |
| EXP21 — logistic, state + context | 0.1597 | 0.4796 |
| EXP22 — LightGBM, state only | 0.1726 | 0.5141 |
| EXP23 — LightGBM, state + context | 0.1596 | 0.4790 |
| **EXP24 — LightGBM, state + context + momentum** | **0.1562** | **0.4701** |

Every ML configuration beats Markov; EXP24 wins clearly (15.1% lower
Brier, 15.7% lower log-loss). The more interesting finding is in the
representation comparison, not the headline number: **which features are
included matters far more than model family** — EXP21 (linear) and EXP23
(trees) score within noise of each other on the same features, while
adding context features (EXP20→EXP21) roughly doubled the improvement
switching model family alone gave (EXP20→EXP22). See
[EXP23](../../experiments/EXP23-lightgbm-state-context.md) for the full
finding.

EXP24 shows some overfitting on untuned defaults (train Brier 0.1165 vs
test 0.1562) — reported rather than hidden; hyperparameter tuning is a
genuine follow-up, not yet done. See
[EXP24](../../experiments/EXP24-lightgbm-state-context-momentum.md).
