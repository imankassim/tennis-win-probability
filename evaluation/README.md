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
