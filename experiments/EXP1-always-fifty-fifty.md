# EXP1 — Always-50/50 probability

- Status: Retained
- Depends on: none
- Date: 2026-09-08

## Hypothesis

Not a hypothesis in the usual sense — this is the floor, not a candidate.
Every later component must be measurably better than always guessing 0.5,
or it has added complexity for nothing.

## Configuration

`pricing/baselines/heuristics.py::always_fifty_fifty()`. Takes no inputs,
returns `0.5` unconditionally.

## Metrics

Evaluated with `evaluation/harness.py` (Journey 8) against every point of
every match with a confirmed outcome in the real ingested sample (183
matches, 27,999 points):

| Metric | Value |
|---|---|
| Brier score | 0.2500 |
| Log-loss | 0.6931 |

Exactly the theoretical constants (Brier = 0.25, log-loss = ln 2), as
expected — nothing about the data can move them, which is exactly why this
is a useful, stable floor. Also exercised by unit tests
(`tests/unit/test_baselines.py`) confirming it is state-independent.

## Decision

Retained, permanently, as the baseline every other experiment is compared
against. Per the negative-result policy, it is never "rejected" — the
point of a floor is that it stays.

## Known failure

Carries zero information about the actual match. This is the failure by
design, recorded here per the "primitive baselines, with failures
recorded" journey exit criterion — not a defect to fix.
