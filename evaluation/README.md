# evaluation

Metrics, evaluation harness and latency reporting used to compare
configurations fairly (Journey 8).

## Status

Complete: Brier score, log-loss, latency percentiles, and a harness that
scores any probability function against every point of every match with a
confirmed outcome. Calibration error (ECE) and reliability diagrams are
not built yet — they belong to Journey 13 (calibration), once there's a
calibration layer to diagnose.

## Structure

- `metrics.py` — `brier_score`, `log_loss`, `percentile`. Pure functions,
  no dependency on any estimator or repository.
- `harness.py` — `evaluate_configuration(name, probability_fn, matches,
  points_by_match, outcomes)`: scores a probability function at every
  point of every match with a confirmed outcome. Matches without one
  (quarantined as incomplete) are excluded, not guessed at.
- `latency_report.py` — reads the quote event log
  (`backend/event_log.py`) and reports median/p95 latency.
- `evaluate_markov.py` — a Markov-specific evaluator, separate from
  `harness.py` because the Markov engine needs per-match context
  (best_of, server, per-match serve rates) that `harness.py`'s simpler
  `(sets_a, sets_b, games_a, games_b) -> probability` signature can't
  express. Reuses `metrics.py`, so results are directly comparable.

No match-level train/test split yet: EXP1/EXP2 are fixed, untuned
heuristics, and the Markov serve-rate estimators are direct empirical
counts, not fitted parameters — nothing here has been tuned against this
same data yet. Splitting starts to matter once something actually is
(e.g. sweeping the shrinkage strength in EXP13) — see
[docs/architecture/offline-training-architecture.md](../docs/architecture/offline-training-architecture.md).

## Real evidence (EXP1 vs EXP2 vs Markov)

Run against the full ingested archive: 5,568 matches / 904,513 points
(the 2010s and 2020s Match Charting Project points files — see
[database/README.md](../database/README.md#ingestion-evidence)), of which
5,453 matches / 890,356 points produced a confirmed outcome through the
full ingestion pipeline including data-quality gates:

| Configuration | Brier score | Log-loss |
|---|---|---|
| EXP1 (always 50/50) | 0.2500 | 0.6931 |
| EXP2 (score-leader heuristic) | 0.1934 | 0.5737 |
| Markov (EXP11/13, shrunk serve rates) | 0.1839 | 0.5579 |

EXP2 clearly beats the floor (22.6% lower Brier, 17.2% lower log-loss than
EXP1). The Markov engine beats EXP2 by a real, credible margin too (4.9%
lower Brier, 2.8% lower log-loss) — a first pass against a smaller,
bounded sample (183 matches) showed only a marginal gap, investigated
rather than accepted at face value: traced to 45% of that sample's
matches having a player with zero prior serve history. Ingesting the full
archive dropped that to 10.6% and widened the gap as hypothesised — see
[experiments/EXP11-per-player-serve-rate.md](../experiments/EXP11-per-player-serve-rate.md)
and [pricing/markov/README.md](../pricing/markov/README.md).

Getting the bulk evaluation to run at this scale also surfaced two real
performance bugs in `pricing/markov/`, both fixed and covered by
regression tests: an unbounded `lru_cache` causing garbage-collector
slowdown, and unbounded recursion for historical advantage-set matches
(pre-2022-era deciding sets with no tiebreak at 6-6).

## Real evidence (Markov vs the ML candidates, EXP20-24)

Every ML configuration beats the Markov comparator on the same test
methodology (a chronological, match-level held-out split this time,
rather than evaluating the whole archive — see
[pricing/ml/README.md](../pricing/ml/README.md) for the full table).
The leading candidate (EXP24, LightGBM with state + context + momentum
features) beats Markov by 15.1% lower Brier score, 15.7% lower log-loss —
computed independently alongside Markov and blended (Journey 12) rather
than replacing it, now wired into the live API as of Journey 17 (see
[pricing/README.md](../pricing/README.md)).

## Real evidence (the blend, EXP30-33)

Naively averaging the two estimates at a fixed 50/50 weight (EXP32) is
*worse* than using ML alone — a concrete demonstration of why blending
isn't automatically an improvement. Only a weight tuned on a validation
set (never the final test set — EXP33, landing on mostly trusting ML)
recovers a real, if modest, edge over ML alone. See
[pricing/blend/README.md](../pricing/blend/README.md).

## Real evidence (calibration, EXP40-43)

Isotonic regression clearly improves calibration error (ECE) over the raw
blend, and doing it per match phase (early/mid/deciding set) improves it
further (55% lower ECE than no calibration). Platt scaling, the "standard"
calibration method, makes things *worse* here on every metric — a genuine
negative result, not a modelling mistake: the blend's raw output was
already reasonably well-calibrated, and Platt's fixed logistic-shape
correction distorted rather than fixed it. See
[pricing/calibration/README.md](../pricing/calibration/README.md).

## Real evidence (the meta-model, EXP34)

Rejected: a learned combiner (stacking the Markov and ML outputs with
the raw features) underperformed the simple tuned blend (EXP33) in
every variant tried, some badly enough to score worse than Markov alone.
Diagnosed as overfitting — 716,025 point-rows come from only 4,363
independent matches, far less real signal for a many-parameter model
than the row count suggests. See
[pricing/blend/README.md](../pricing/blend/README.md).

## Real evidence (value-detection backtest, EXP15)

621 real matches with both a confirmed outcome and matched 2025-2026 ATP
odds (tennis-data.co.uk). Our best model (the blend) scores a clearly
worse pre-match Brier than the de-vigged market (0.1984 vs 0.1828) — the
expected, honest result, not a "beat the market" claim (none was made).
Context features do meaningfully close the gap versus serve-rate-only
Markov alone (0.2305 → 0.1984). See
[trading_rules/README.md](../trading_rules/README.md).
