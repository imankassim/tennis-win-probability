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

Run against 183 real matches / 27,999 points (the same ingested sample
used in Journey 4):

| Configuration | Brier score | Log-loss |
|---|---|---|
| EXP1 (always 50/50) | 0.2500 | 0.6931 |
| EXP2 (score-leader heuristic) | 0.1831 | 0.5515 |
| Markov (EXP11/13, shrunk serve rates) | 0.1829 | 0.5453 |

EXP2 clearly beats the floor (26.8% lower Brier, 20.4% lower log-loss than
EXP1). The Markov engine beats EXP2 too, but only marginally on Brier
score — investigated rather than accepted at face value, see
[experiments/EXP11-per-player-serve-rate.md](../experiments/EXP11-per-player-serve-rate.md)
for the finding (45% of sampled matches have a player with zero prior
serve history in our bounded ingestion sample) and
[pricing/markov/README.md](../pricing/markov/README.md).
