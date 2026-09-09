# EXP24 - XGBoost/LightGBM classifier, state, context and momentum features

- Status: Retained - this is the ML journey's leading configuration
- Depends on: EXP23
- Date: 2026-09-08

## Hypothesis

Within-match momentum (the fraction of the last 10 points a player has
won *in this match*, `pricing/ml/features.py::_momentum`) is a genuinely
different signal from cross-match context (form/surface/h2h/Elo, all
computed as of before this match started) - it should add real
information a purely pre-match feature set can't have.

## Configuration

Same as EXP23 (state + context) plus `momentum_a`. Same train/test
split, same LightGBM settings.

## Metrics

| Configuration | Brier score | Log-loss |
|---|---|---|
| Markov (comparator) | 0.1839 | 0.5579 |
| EXP23 (LightGBM, state + context) | 0.1596 | 0.4790 |
| **EXP24 (LightGBM, state + context + momentum)** | **0.1562** | **0.4701** |

Beats EXP23 by 2.1% lower Brier - a real, if modest, gain from momentum
alone - and beats Markov overall by **15.1% lower Brier score, 15.7%
lower log-loss**: the clearest margin of any configuration tested.

**Overfitting check** (train-set Brier vs the held-out test-set Brier
above, same model): train 0.1165 vs test 0.1562 - a real gap, meaning
the untuned defaults (`n_estimators=100, max_depth=6`, no other
regularisation) do overfit somewhat. Reported honestly rather than
hidden: the test-set number is still the one that matters for
generalisation, and it's the number reported here and used for
comparison - but hyperparameter tuning (fewer/shallower trees, L1/L2
regularisation, early stopping against a validation slice) is a genuine
follow-up, not yet done.

## Decision

**Retained as the leading ML candidate.** Not yet wired into the live API
- per the logical architecture, the Markov and ML estimates are meant to
be computed independently and then blended (Journey 12), not one
replacing the other. This experiment's job (Journey 11's exit outcome,
"data-driven candidate estimate") is done: EXP24 is that candidate.
