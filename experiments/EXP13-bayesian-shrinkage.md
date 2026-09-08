# EXP13 — Bayesian shrinkage for low-sample players

- Status: Retained
- Depends on: EXP11
- Date: 2026-09-08

## Hypothesis

A pure per-player empirical serve rate (EXP11) is undefined or unreliable
for players with little or no prior data — exactly the sparse-data risk
already named in `docs/architecture/risk_register.md`. Shrinking each
player's estimate toward the tour average, weighted by how much data they
actually have, should be strictly safer with no accuracy cost when data is
plentiful.

## Configuration

`pricing/markov/serve_rate.py::serve_rate_with_shrinkage()`:
`(player_won + k * tour_avg) / (player_served + k)`, a standard
pseudo-count estimator with `k = 20` (`DEFAULT_SHRINKAGE_STRENGTH`,
untuned — chosen as roughly "20 service points' worth of trust in the
prior", not fitted to held-out data). A player with zero prior data
returns exactly the tour average; a well-covered player ends up close to
their own empirical rate.

## Metrics

This is the configuration actually evaluated and reported in
[EXP11](EXP11-per-player-serve-rate.md)'s metrics table (Brier 0.1829,
log-loss 0.5453 vs EXP2's 0.1831 / 0.5515) — EXP11 and EXP13 were
evaluated together since a pure, unshrunk per-player rate isn't a usable
configuration on its own (undefined for ~45% of matches in the sample).

## Decision

Retained. Directly addresses the sparse-data risk from the risk register
with no observed downside. The shrinkage strength (`k=20`) is untuned —
a genuine follow-up experiment would sweep `k` against held-out matches
once the historical ingestion window is large enough for that comparison
to be meaningful (see the follow-up noted in EXP11).
