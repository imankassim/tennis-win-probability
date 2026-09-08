# 6. Separate offline training/calibration from online serving

- Status: Accepted
- Date: 2026-09-08

## Context

Model training, calibration fitting and evaluation are compute-heavy,
iterative and allowed to fail or be re-run; the online `/probability`
request path must be fast, predictable and stable regardless of what is
happening in experimentation. Mixing the two would let a training run
affect live latency, and would make it hard to know which model artefact
actually served a given historical quote.

## Decision

Run model training, calibration fitting and evaluation entirely outside the
live request path (offline training architecture, section 9). Online
serving loads versioned artefacts (Markov parameter sets, ML models,
calibration maps) from a model/configuration registry; it never trains or
fits during a request.

## Consequences

- Every served quote can be tied to an exact `model_version`, satisfying
  FR-04 and the auditability non-functional requirement.
- Retraining or promoting a new model version is a deliberate, reviewed
  registry update (governance: "automatic retraining or model promotion
  without review" is explicitly out of scope), not a side effect of serving
  traffic.
- Requires the feature-generation code to be shared, versioned, and
  identical between the offline training pipeline and the online serving
  path, to avoid train/serve skew — enforced by the training control
  "version feature-generation logic and use the same code in training and
  serving".
