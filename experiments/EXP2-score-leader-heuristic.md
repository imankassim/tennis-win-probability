# EXP2 — Current-score-leader heuristic

- Status: Retained
- Depends on: EXP1
- Date: 2026-09-08

## Hypothesis

Just knowing who is currently ahead on the scoreboard (sets, then games)
should beat always-50/50, even with no knowledge of serve, ranking or
history.

## Configuration

`pricing/baselines/heuristics.py::score_leader_probability(sets_a, sets_b,
games_a, games_b)`. A set lead returns 0.75/0.25; failing that, a game lead
within the current set returns 0.6/0.4; a tie on both returns 0.5. Fixed,
untuned constants — deliberately not fit to data, so it stays a primitive
baseline rather than drifting into the Markov/ML territory.

## Metrics

Evaluated with `evaluation/harness.py` (Journey 8) against the same 183
matches / 27,999 points as EXP1:

| Metric | EXP1 (floor) | EXP2 | Change |
|---|---|---|---|
| Brier score | 0.2500 | 0.1831 | −26.8% |
| Log-loss | 0.6931 | 0.5515 | −20.4% |

Confirms the hypothesis: knowing only who's ahead beats always-50/50 by a
clear margin. Also exercised by unit tests
(`tests/unit/test_baselines.py`) confirming the mechanical behaviour:
ties return 0.5, a set lead dominates a game deficit, and the function is
symmetric between the two players.

## Decision

Retained as the second rung of the baseline floor, above EXP1 and below
the Markov chain (Journey 9). It clearly beats EXP1, as expected; it is
expected to be clearly beaten by the Markov baseline in turn — if it
isn't, that would itself be a finding worth investigating before building
anything more advanced.

## Known failures

Recorded per the "primitive baselines, with failures recorded" journey
exit criterion — these are exactly the target model scenarios (see
`docs/architecture/charter.md`) this heuristic is expected to misprice:

- **Ignores server.** Identical score lines get identical probabilities
  whether the leader is serving or receiving, so it misprices routine
  holds and break points the same way.
- **Discontinuous, not proportional.** A single game changes the estimate
  by a fixed jump (0.5 → 0.6, or 0.6 → 0.75 on levelling a set), so it
  overreacts to one point in a break-point-pressure scenario instead of
  reacting proportionally.
- **No recovery base rates.** A two-sets-down player gets a flat 0.25
  regardless of how often such deficits are actually overcome, so it
  misprices deciding-set recovery.
- **No player context.** Ranking, recent form and surface are invisible to
  it, so it misprices a favourite trailing early against a big outsider —
  the heuristic reads it exactly the same as any other early deficit.
