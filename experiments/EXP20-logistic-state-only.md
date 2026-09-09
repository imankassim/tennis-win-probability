# EXP20 - Logistic regression on score-state features only

- Status: Retained
- Depends on: EXP9 (Markov baseline, as the comparator)
- Date: 2026-09-08

## Hypothesis

A simple learned model, given nothing but the score state (sets, games,
server, best_of) - the same information Markov uses - should still learn
useful non-linear-ish patterns a fixed formula can't, and serves as the
floor for the ML journey the way EXP1 serves as the floor for the whole
project.

## Configuration

`pricing/ml/train.py::train_and_evaluate("EXP20_logistic_state",
"logistic", STATE_FEATURES, ...)` - scikit-learn `LogisticRegression`
(features standardised first - see EXP21's note on why), trained on
`sets_a, sets_b, games_a, games_b, server_is_a, best_of` only. Match-level
chronological split (`match_level_split`, 80/20, most recent 20% held
out) - 4,363 train matches / 1,090 test matches, 715,055 / 175,301
points.

## Metrics

Evaluated on the held-out test set (never seen during training):

| Configuration | Brier score | Log-loss |
|---|---|---|
| Markov (comparator, EXP11/13) | 0.1839 | 0.5579 |
| EXP20 (logistic, state only) | 0.1744 | 0.5208 |

Beats Markov by 5.2% lower Brier, 6.7% lower log-loss - a real
improvement from just letting the state→outcome relationship be learned
rather than derived from a fixed serve-probability formula, even with no
extra information over what Markov already sees.

## Decision

Retained as the ML journey's floor. Confirms state-only learning already
adds something; EXP21-24 test how much more context and a different model
family add on top.
