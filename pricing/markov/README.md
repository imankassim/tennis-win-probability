# pricing/markov

Transparent, analytic point/game/set/match Markov chain model
(Klaassen & Magnus, 2003). Point-to-match win probability from each
player's estimated serve-win rate.

## Status

Journey 9 (Markov baseline) is complete and wired into the API as the
default estimator, replacing the score-leader heuristic (EXP2) from
Journey 5.

## Structure

- `formulas.py` - the recursive `prob_win_game` / `prob_win_tiebreak` /
  `prob_win_set` / `prob_win_match` formulas. Pure math, no data
  dependency; verified against known mathematical properties (symmetry,
  the deuce closed form, and - via an independent Monte Carlo simulation -
  the fact that who serves first doesn't affect a fresh set's outcome).
  `prob_win_tiebreak` and `prob_win_set` are truncated past a combined
  score depth (documented in-module): neither has a closed form for an
  evenly-matched extended tiebreak or advantage set, so without a cap the
  recursion is mathematically unbounded - caught for real from a
  `RecursionError` while bulk-evaluating real historical data.
- `serve_rate.py` - EXP10 (tour average), EXP11 (per-player empirical
  rate), EXP13 (Bayesian shrinkage toward the tour average, weighted by
  sample size), all computed from our own ingested match archive with
  strict no-look-ahead. `bulk_shrunk_serve_rates()` computes the same
  EXP13 values for every match in one archive pass (O(points), not
  O(matches × archive size)) - the per-match function alone makes bulk
  evaluation quadratic.
- `engine.py` - ties the two together: `estimate_match_serve_rates()` and
  `markov_probability()`.

## Real evidence

Evaluated with `evaluation/evaluate_markov.py` against the full ingested
archive: 5,568 matches / 904,513 points, of which 5,453 matches / 890,356
points produced a confirmed outcome through the full pipeline including
data-quality gates:

| Configuration | Brier score | Log-loss |
|---|---|---|
| EXP1 (always 50/50) | 0.2500 | 0.6931 |
| EXP2 (score-leader heuristic) | 0.1934 | 0.5737 |
| Markov (EXP11/13, shrunk serve rates) | 0.1839 | 0.5579 |

Beats EXP2 by a real, credible margin (4.9% lower Brier, 2.8% lower
log-loss). A first pass against a smaller, bounded sample (183 matches)
showed only a marginal gap - investigated rather than accepted at face
value (see [EXP11](../../experiments/EXP11-per-player-serve-rate.md) for
the full finding): 45% of that sample's matches had a player with zero
prior serve history, forcing heavy reliance on the tour-average fallback.
Ingesting the full 2010s+2020s Match Charting Project points files
dropped that to 10.6% and widened the gap as hypothesised. The formulas
themselves are independently verified correct throughout.

Running the evaluation at this scale also surfaced and fixed two real
bugs: an unbounded `lru_cache` causing garbage-collector-driven
super-linear slowdown (200 matches: 1s; 2,000 matches: 93s, before the
fix), and unbounded recursion for historical advantage-set matches. Both
are covered by regression tests.
