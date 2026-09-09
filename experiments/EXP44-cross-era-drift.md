# EXP44 - Cross-era drift check

- Status: Retained (diagnostic finding, not a promote/reject decision)
- Depends on: EXP24 (ML model), EXP33 (blend), EXP43 (calibration) - scores the already-promoted `blend_v1_calibrated` pipeline, does not refit anything
- Date: 2026-09-09

## Hypothesis

The risk register (docs/architecture/risk_register.md) names "overfitting
to a particular rule or equipment era" as a real risk: a model that looks
strong on the era it was mostly trained on could generalise poorly to a
meaningfully different one (scoring formats, equipment, the general level
of the tour all shift over 15+ years). If the promoted pipeline's
accuracy and calibration hold up evenly across the 2010s and 2020s halves
of the archive, that's evidence against this risk; if they diverge
sharply, that's a genuine finding worth knowing before trusting the
model's numbers uncritically.

## Configuration

`evaluation/drift_check.py`'s `score_full_pipeline` scores the promoted
`blend_v1_calibrated` artefact (unmodified - Markov + ML computed
independently, blended at EXP33's weight, phase-calibrated by EXP43)
against every point of every match with a confirmed outcome in the full
archive: 5,457 matches / 891,514 points. `split_by_era` then buckets the
already-scored results at 2020-01-01 - matching the same 2010s/2020s
boundary the source ingestion files themselves use
(`charting-m-points-2010s-full.csv` / `charting-m-points-2020s-full.csv`,
see database/README.md).

Scoring happens on the whole archive in one pass, not on two archives
scored separately - `bulk_shrunk_serve_rates` and
`compute_match_context_features` build running per-player history in
date order, so scoring the 2020s era in isolation would lose all of the
2010s era's history, which isn't what live serving would actually see.

## Metrics

| Era | Matches | Points | Brier score | Log-loss | ECE |
|---|---|---|---|---|---|
| 2010s (pre-2020) | 2,182 | 351,440 | 0.1183 | 0.3718 | 0.0455 |
| 2020s (2020+) | 3,275 | 540,074 | **0.1312** | **0.4067** | **0.0350** |

**Not a clean split, and the result needs that caveat to be read
correctly.** `pricing/promote_model.py` trains the ML model on the
chronologically older 85% of *all* matches and calibrates on the newest
15% - so most of the "2020s" bucket above was still in the ML model's
own training data, and only its most recent slice (the 818-match
calibration holdout) is genuinely held out from everything. This isn't
an era-holdout design (train on one era, test on the other); it's a
recency-holdout design. That confound predicts exactly the pattern seen
here: **accuracy (Brier, log-loss) is worse on the 2020s bucket** - a
mix of in-sample training matches and a smaller genuinely-unseen slice
scores worse on average than the 2010s bucket, which the model saw
proportionally more of, closer to in-sample fit - while **calibration
(ECE) is better on the 2020s bucket**, because the phase calibrator was
fit on exactly that bucket's most recent slice, giving it a natural
home-field advantage there specifically.

## Decision

**Retained as a diagnostic finding, not a promotion decision** - nothing
here changes what's served; EXP44 exists to check the promoted pipeline
for a specific, named risk, not to compare candidate configurations.
No sharp cliff or collapse was found in either era (Brier stays well
below EXP1's 0.25 floor and EXP2's 0.1934 comparator in both buckets),
so this doesn't surface an urgent problem. But the accuracy gap (0.1183
vs 0.1312 Brier, a real ~11% relative difference) is large enough that it
shouldn't be waved away as noise either, and the recency-holdout /
era-holdout confound above means this check can't yet distinguish
"genuine era drift" from "the model simply saw more of the older data."
**A cleaner test would hold out an entire era from training** (e.g. train
only on pre-2023 matches, evaluate purely on 2023+), which
`pricing/promote_model.py` doesn't currently support - its split is
purely by recency, not by a chosen boundary. Recorded here as a concrete
follow-up rather than built now, since it would mean training a second,
non-served model purely for this diagnostic.
