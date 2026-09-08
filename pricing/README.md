# pricing

Every probability-estimation layer (Markov, ML, blend, calibration) plus
the promotion script that bundles them into one artefact for live serving
(Journey 17).

## Status

Journey 17 (full API integration) is complete. Each layer was built and
evaluated offline first, in its own sub-package — see
[markov/README.md](markov/README.md), [ml/README.md](ml/README.md),
[blend/README.md](blend/README.md),
[calibration/README.md](calibration/README.md) for the real evidence
behind each one. This README covers only the piece that ties them
together for serving.

## Structure

- `promote_model.py` — trains and packages the pipeline: the EXP24 ML
  model (fit on the chronologically older 85% of matches), the EXP43
  phase calibrator (fit on blended predictions for the newer 15% — held
  out from the ML model's own training, so it measures genuine
  out-of-sample miscalibration, not the model's fit to its own training
  set), and the EXP33 blend weight, bundled into a `PricingArtefacts`
  dataclass and persisted via `joblib` to
  `docs/model_cards/artefacts/pricing_pipeline.joblib` (gitignored — a
  build product, not source). Deliberately **not** automatic — per
  [docs/architecture/charter.md](../docs/architecture/charter.md)'s "no
  automatic retraining or model promotion without review", this is a
  script a person runs on purpose. Running it *is* the review: the
  feature set, blend weight and calibration method it packages were
  already decided by experiments/EXP20-24, EXP32-33 and EXP40-43: this
  script doesn't re-derive them.
- `run_promotion.py` — the CLI entry point (`python -m
  pricing.run_promotion <matches.csv> <points1.csv> [...]`). Kept
  separate from `promote_model.py` deliberately: running
  `promote_model.py` directly with `python -m` would load it as
  `__main__`, and `joblib`/`pickle` locate a class by the module it's
  reachable from in `sys.modules` — a `PricingArtefacts` pickled while
  its own defining module was loaded as `__main__` can't be unpickled
  later by a normal `import pricing.promote_model` (e.g.
  `backend/main.py` at startup, in a different process, where the class
  was never imported under the name `__main__`). This bit — running the
  training script directly, then failing to load the artefact from the
  API process — is a real bug this project hit once, not a hypothetical
  one; splitting the CLI out fixes it structurally rather than needing
  everyone who runs the script to remember a workaround.

## Running the promotion

```bash
python -m pricing.run_promotion \
  data/raw/match_charting_project/charting-m-matches.csv \
  data/raw/match_charting_project/charting-m-points-2010s-full.csv \
  data/raw/match_charting_project/charting-m-points-2020s-full.csv
```

Run against the full archive: 4,639 training matches, 818 held-out
calibration matches, ~40s end to end.

## How the live API uses this

`backend/probability.py` loads the artefact (if one exists) once at
startup. For each `/probability` request it computes the Markov estimate
and the ML estimate independently (state + context + within-match
momentum, the same features `pricing/ml/features.py` builds for
training — context features come from a bulk cache built once at startup
with the exact same `compute_match_context_features` function the
promotion script trained against, so a live request scores the identical
feature the model learned from), blends them at the promoted weight, and
applies the promoted phase calibrator — `model_version` becomes the
artefact's own version string (`blend_v1_calibrated`),
`fallback_used=false`.

If no artefact exists — a fresh clone, or before anyone has run the
promotion script — the API degrades gracefully to the Markov engine
alone: `model_version="markov_v1"`, `fallback_used=true`. This is the
graceful-degradation behaviour
[docs/architecture/logical-architecture.md](../docs/architecture/logical-architecture.md)'s
`fallback_used` flag documents, not an error path; both branches are
covered by `tests/integration/test_api.py` (which checks its own live
`_artefacts` state rather than hardcoding one outcome, since the artefact
file is gitignored and may or may not exist depending on whether someone
has run the promotion script on that checkout) and were verified directly
against a running server for both cases.
