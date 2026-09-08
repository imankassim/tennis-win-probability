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

No match-level train/test split yet: EXP1 and EXP2 are fixed, untuned
heuristics with nothing to overfit. Splitting starts to matter once a
configuration is actually fitted to data (Journey 9's Markov parameter
tuning onward) — see
[docs/architecture/offline-training-architecture.md](../docs/architecture/offline-training-architecture.md).

## Real evidence (EXP1 vs EXP2)

Run against 183 real matches / 27,999 points (the same ingested sample
used in Journey 4):

| Configuration | Brier score | Log-loss |
|---|---|---|
| EXP1 (always 50/50) | 0.2500 | 0.6931 |
| EXP2 (score-leader heuristic) | 0.1831 | 0.5515 |

EXP2 clearly beats the floor (26.8% lower Brier, 20.4% lower log-loss),
confirming its hypothesis. See
[experiments/EXP1-always-fifty-fifty.md](../experiments/EXP1-always-fifty-fifty.md)
and
[experiments/EXP2-score-leader-heuristic.md](../experiments/EXP2-score-leader-heuristic.md).
This is the same harness the Markov baseline (Journey 9) will be measured
against, and is expected to clearly beat EXP2 in turn.
