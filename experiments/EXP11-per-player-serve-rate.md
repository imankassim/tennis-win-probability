# EXP11 - Per-player overall serve-win rate

- Status: Retained
- Depends on: EXP10
- Date: 2026-09-08 (updated same day, after a larger ingestion - see Metrics)

## Hypothesis

Feeding each player's own empirical serve-win rate into the Markov
formulas, instead of one constant tour-average rate, should meaningfully
improve accuracy - better servers should be recognised as such.

## Configuration

`pricing/markov/serve_rate.py::player_serve_rate()` - each player's own
`points_won_on_serve / points_served` from real ingested matches strictly
before the match being predicted (no look-ahead). Used directly (without
shrinkage) would be EXP11 in isolation; what's actually evaluated and
wired into the API is EXP13 (shrinkage), since a pure per-player estimate
with no fallback is unusable for a player with sparse or zero prior data -
exactly the risk this experiment surfaced (see Metrics).

## Metrics

First evaluated against a bounded ~3MB ingestion sample (183 matches /
27,999 points): Markov beat EXP2 only marginally (Brier 0.1829 vs 0.1831).
Per the "if it isn't [clearly beaten], that's worth investigating" note in
EXP2's write-up, this was investigated rather than accepted at face value
- traced to 45% of matches having a player with zero prior serve history
in that small sample. Follow-up: ingested the full 2010s and 2020s
Match Charting Project points files (904,513 points across 5,568 matches;
run through the full ingestion pipeline including data-quality gates,
5,453 matches produced a confirmed outcome - up from 27,999 points / 183
matches) and re-ran the comparison on the 890,356 points belonging to
those 5,453 matches:

| Configuration | Brier score | Log-loss |
|---|---|---|
| EXP1 (always 50/50) | 0.2500 | 0.6931 |
| EXP2 (score-leader heuristic) | 0.1934 | 0.5737 |
| EXP11/13 (Markov, shrunk serve rates) | 0.1839 | 0.5579 |

With the larger archive, the zero-history rate dropped from 45% to 10.6%
of matches, and the gap widened as hypothesised: Markov now beats EXP2 by
4.9% on Brier score and 2.8% on log-loss - a real, credible margin, not
the near-tie the small sample showed. (EXP2's own score moved too: 0.1934
vs the small sample's 0.1831 - the larger, more varied archive, spanning
Challenger and qualifying rounds as well as tour level, is a harder
prediction task on average, which is exactly why a bigger, more
representative evaluation set matters.)

## Decision

Retained, wired into the API as the default estimator (replacing EXP2).
The original marginal result led to a real, useful follow-up (a larger
ingestion) rather than being accepted or dismissed at face value - the
gap is now a credible, evidenced improvement over EXP2, consistent with
gate G5's "is the analytic model a credible tuned baseline?".
