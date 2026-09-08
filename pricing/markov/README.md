# pricing/markov

Transparent, analytic point/game/set/match Markov chain model
(Klaassen & Magnus, 2003). Point-to-match win probability from each
player's estimated serve-win rate.

## Status

Journey 9 (Markov baseline) is complete and wired into the API as the
default estimator, replacing the score-leader heuristic (EXP2) from
Journey 5.

## Structure

- `formulas.py` — the recursive `prob_win_game` / `prob_win_tiebreak` /
  `prob_win_set` / `prob_win_match` formulas. Pure math, no data
  dependency; verified against known mathematical properties (symmetry,
  the deuce closed form, and — via an independent Monte Carlo simulation —
  the fact that who serves first doesn't affect a fresh set's outcome).
- `serve_rate.py` — EXP10 (tour average), EXP11 (per-player empirical
  rate), EXP13 (Bayesian shrinkage toward the tour average, weighted by
  sample size), all computed from our own ingested match archive with
  strict no-look-ahead.
- `engine.py` — ties the two together: `estimate_match_serve_rates()` and
  `markov_probability()`.

## Real evidence

Evaluated with `evaluation/evaluate_markov.py` against the same 183
matches / 27,999 points as EXP1/EXP2:

| Configuration | Brier score | Log-loss |
|---|---|---|
| EXP1 (always 50/50) | 0.2500 | 0.6931 |
| EXP2 (score-leader heuristic) | 0.1831 | 0.5515 |
| Markov (EXP11/13, shrunk serve rates) | 0.1829 | 0.5453 |

Beats EXP2, but only marginally on Brier score — investigated rather than
accepted at face value (see [EXP11](../../experiments/EXP11-per-player-serve-rate.md)
for the full finding): 45% of matches in our bounded ingestion sample have
at least one player with zero prior serve history, forcing heavy reliance
on the tour-average fallback. The formulas themselves are independently
verified correct; this is a data-coverage limitation, not a modelling
flaw. Follow-up: ingest a larger historical window and re-run the
comparison.
