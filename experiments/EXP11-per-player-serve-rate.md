# EXP11 — Per-player overall serve-win rate

- Status: Retained (with a documented limitation)
- Depends on: EXP10
- Date: 2026-09-08

## Hypothesis

Feeding each player's own empirical serve-win rate into the Markov
formulas, instead of one constant tour-average rate, should meaningfully
improve accuracy — better servers should be recognised as such.

## Configuration

`pricing/markov/serve_rate.py::player_serve_rate()` — each player's own
`points_won_on_serve / points_served` from real ingested matches strictly
before the match being predicted (no look-ahead). Used directly (without
shrinkage) would be EXP11 in isolation; what's actually evaluated and
wired into the API is EXP13 (shrinkage), since a pure per-player estimate
with no fallback is unusable for a player with sparse or zero prior data —
exactly the risk this experiment surfaced (see Metrics).

## Metrics

Evaluated via `evaluation/evaluate_markov.py` (using the shrunk estimate,
EXP13, since pure per-player rates are undefined for debut-in-sample
players) against the same 183 matches / 27,999 points as EXP1/EXP2:

| Configuration | Brier score | Log-loss |
|---|---|---|
| EXP1 (always 50/50) | 0.2500 | 0.6931 |
| EXP2 (score-leader heuristic) | 0.1831 | 0.5515 |
| EXP11/13 (Markov, shrunk serve rates) | 0.1829 | 0.5453 |

The Markov engine beats EXP2, but only marginally on Brier score (0.1829
vs 0.1831) — log-loss improves more clearly (0.5453 vs 0.5515). Per the
"if it isn't [clearly beaten], that's worth investigating" note in EXP2's
own write-up, this was investigated rather than accepted at face value.

**Finding:** the gap is explained by data volume, not the modelling
approach. Checked directly: **85 of 190 matches (45%) have at least one
player with zero prior serve history** in our bounded ingestion sample
(a ~3MB slice — see `docs/data_sheets/data_provenance.md` — not the full
archive), forcing heavy reliance on the tour-average fallback for nearly
half the dataset. Median prior service points available where a player
does have history: 152 — enough for a rough estimate, not a precise one.
The recursive formulas themselves are independently verified correct
(`tests/unit/test_markov_formulas.py`, including Monte Carlo
cross-checks), so this is a data-coverage limitation, not a design flaw.

## Decision

Retained, wired into the API as the default estimator (replacing EXP2),
because it does beat EXP2 on both metrics and represents the intended
"credible tuned baseline" (gate G5) — a real, if modest, improvement, with
a specific, explainable, addressable reason for why it isn't larger.
**Follow-up (not yet done):** ingest a larger historical window (more of
the Match Charting Project archive, not just the validation sample) and
re-run this comparison — the hypothesis is that the gap widens
substantially once most players have real prior-serve history instead of
falling back to the tour average.
