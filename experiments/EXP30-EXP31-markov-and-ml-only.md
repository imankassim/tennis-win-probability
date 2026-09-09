# EXP30 / EXP31 - Markov-only and ML-only (blend comparators)

- Status: Retained (as comparators, not candidates for serving alone)
- Depends on: EXP9 (Markov baseline), EXP24 (leading ML candidate)
- Date: 2026-09-08

## Hypothesis

Not new hypotheses - EXP30 (Markov-only) and EXP31 (ML-only, EXP24) are
the two ends of the blend weight (`markov_weight=1.0` and `0.0`
respectively), evaluated on the exact same validation/test split as
EXP32/33 so all four numbers are directly comparable.

## Configuration

The held-out test set from Journey 11 (1,090 matches) was itself split
in half chronologically: a validation half (545 matches, for EXP33's
weight tuning) and a final test half (545 matches, for the numbers
reported here and in EXP32/33). Markov predictions use
`pricing/markov/serve_rate.py::bulk_shrunk_serve_rates` and
`pricing/markov/engine.py::markov_probability`; ML predictions are EXP24
(LightGBM, state + context + momentum), trained on the original training
set.

## Metrics

On the final-test half (88,305 points / 545 matches):

| Configuration | Brier score | Log-loss |
|---|---|---|
| EXP30 (Markov-only) | 0.1686 | 0.5061 |
| EXP31 (ML-only, EXP24) | 0.1500 | 0.4540 |

(These differ slightly from EXP9/EXP24's own reported numbers, which were
measured on the full test set rather than this half of it - same models,
smaller evaluation slice.)

## Decision

Retained as comparators. See [EXP32/33](EXP32-EXP33-blend.md) for what
blending them achieves - and doesn't.
