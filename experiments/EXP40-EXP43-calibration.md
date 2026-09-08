# EXP40 / EXP41 / EXP42 / EXP43 — Calibration methods

- Status: EXP40 retained as comparator; EXP41 rejected (retained as evidence); EXP42 retained; EXP43 retained — leading configuration
- Depends on: EXP33 (the tuned blend, the input calibration is applied to)
- Date: 2026-09-08

## Hypothesis

The blend's raw output, while accurate, isn't necessarily well-calibrated
(a 70% quote should be right about 70% of the time — accuracy and
calibration are different properties). Fitting a calibration mapping
should reduce calibration error (ECE) without materially hurting
accuracy (Brier/log-loss).

## Configuration

`pricing/calibration/calibration.py`: `NoCalibration` (EXP40, the raw
blend unchanged), `PlattCalibrator` (EXP41, logistic regression on the
raw probability), `IsotonicCalibrator` (EXP42, a monotonic non-parametric
mapping), `PhaseCalibrator` (EXP43, a separate `IsotonicCalibrator` per
`match_phase` — early/mid/deciding set — falling back to one global
calibrator for a sparse phase).

Fit on the same validation half used to tune EXP33's blend weight
(86,977 points), evaluated on the same final-test half (88,512 points) —
never the same data a calibrator is fit and scored on.

## Metrics

| Configuration | Brier score | Log-loss | ECE |
|---|---|---|---|
| EXP40 (no calibration) | 0.1518 | 0.4587 | 0.0249 |
| EXP41 (Platt scaling) | 0.1531 | 0.4661 | 0.0366 |
| EXP42 (isotonic regression) | 0.1515 | 0.4537 | 0.0153 |
| **EXP43 (phase-level isotonic)** | **0.1511** | 0.4611 | **0.0113** |

**Finding, and not the expected one: Platt scaling makes calibration
*worse*, not better** — ECE rises from 0.0249 to 0.0366, and both
accuracy metrics worsen too. The blend's raw output was already
reasonably well-calibrated to begin with (a log-loss-trained ML model
blended with a probabilistically-grounded analytic model tends to start
that way), and Platt's fixed logistic-shape correction appears to distort
rather than fix whatever small miscalibration was there. Isotonic
regression (EXP42), being non-parametric, doesn't have that failure mode
and clearly helps (39% lower ECE than EXP40). Phase-level isotonic
(EXP43) helps most (55% lower ECE than EXP40, and the best Brier score of
all four) — different match phases genuinely do have different
calibration profiles, confirming the charter's phase-based error
breakdown is picking up something real, not just an arbitrary split.

EXP43's log-loss (0.4611) is slightly worse than EXP42's (0.4537) despite
winning on ECE and Brier — a reminder that these three metrics don't
always agree, and no single one should be read in isolation.

## Decision

**EXP40 retained as the comparator.** **EXP41 rejected** — actively
worse on every metric measured, kept as evidence for why "the standard
calibration method" isn't automatically the right one; the negative-result
policy exists for exactly this. **EXP42 retained** as a solid, simpler
alternative. **EXP43 retained as the leading configuration** — best ECE
and best Brier, and mechanistically well-motivated (calibration genuinely
should vary by match phase). Not yet wired into the live API, for the
same reason as EXP24/EXP33: this is Journey 13's evidence, not a change
to what `/probability` currently serves.
