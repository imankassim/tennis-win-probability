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

Not measured against held-out outcomes yet — the outcome-label set and
evaluation harness are built in Journey 8. Exercised now only by unit
tests (`tests/unit/test_baselines.py`) confirming it is state-independent.
Once Journey 8's harness exists, its Brier score and log-loss on any
balanced evaluation set are fixed, known constants (Brier = 0.25, log-loss
= ln 2 ≈ 0.693), which is exactly why it is useful as a floor: nothing
about the data can make it look better or worse.

## Decision

Retained, permanently, as the baseline every other experiment is compared
against. Per the negative-result policy, it is never "rejected" — the
point of a floor is that it stays.

## Known failure

Carries zero information about the actual match. This is the failure by
design, recorded here per the "primitive baselines, with failures
recorded" journey exit criterion — not a defect to fix.
