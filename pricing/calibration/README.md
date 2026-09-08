# pricing/calibration

Calibration layer mapping the blended probability onto empirically
observed outcome frequencies.

## Status

Journey 13 (calibration) is complete: EXP40-43 evaluated on real data.
`calibration.py` — `NoCalibration`, `PlattCalibrator`,
`IsotonicCalibrator`, `PhaseCalibrator` (a separate isotonic calibrator
per `match_phase`, falling back to a global one for sparse phases). Not
yet wired into the live API, same as the blend and ML layers it sits on
top of.

## Real evidence

Fit on a validation half (86,977 points), evaluated on a held-out final
half (88,512 points) of the blend's output:

| Configuration | Brier score | Log-loss | ECE |
|---|---|---|---|
| EXP40 — no calibration | 0.1518 | 0.4587 | 0.0249 |
| EXP41 — Platt scaling | 0.1531 | 0.4661 | 0.0366 |
| EXP42 — isotonic regression | 0.1515 | 0.4537 | 0.0153 |
| **EXP43 — phase-level isotonic** | **0.1511** | 0.4611 | **0.0113** |

**Not the expected result: Platt scaling makes calibration *worse*, not
better** — worse on all three metrics. The blend's raw output was
already reasonably well-calibrated to start with, and Platt's fixed
logistic-shape correction distorts rather than fixes it. Isotonic
regression (non-parametric, no such failure mode) clearly helps; phase-
level isotonic helps most (55% lower ECE than no calibration), confirming
that calibration genuinely does vary by match phase. See
[EXP40-EXP43-calibration.md](../../experiments/EXP40-EXP43-calibration.md)
for the full write-up, including why EXP41 is marked rejected rather than
just "not chosen".
