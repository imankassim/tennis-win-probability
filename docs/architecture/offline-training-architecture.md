# Offline training and evaluation architecture

```mermaid
flowchart TD
    src["SOURCE DATA\nSackmann Grand Slam point-by-point archive -\nATP/WTA rankings and results -\ntennis-data.co.uk market odds (evaluation benchmark only)"]
    qual["QUALITY & PREPARATION\nSchema checks - provenance - match-level grouping\nfor splits - train/validation/test split"]
    exp["EXPERIMENTS\nMarkov parameter experiments (overall vs surface-specific\nvs shrinkage-adjusted serve-win rates) - ML feature experiments\n(state, player-context, momentum, surface, ranking) -\ncalibration experiments (none vs Platt vs isotonic)"]
    train["MODEL TRAINING\nLogistic baseline - XGBoost/LightGBM classifier -\ngrouped (by-match) evaluation"]
    eval["EVALUATION & ERROR ANALYSIS\nBrier score - log-loss - calibration curve -\nmatch-phase breakdown - comparison against closing market price"]
    reg["MODEL / CONFIGURATION REGISTRY\nVersion - data split - features - metrics -\napproval status - rollback target"]

    src --> qual --> exp --> train --> eval --> reg
```

## Training controls

- Split by match, never by point: a model that has seen the middle of a
  match must never have seen its ending.
- Hold out an entire final set of tournaments as the test set until model
  selection is complete.
- Version feature-generation logic and use the same code in training and
  serving.
- Treat market odds as an evaluation benchmark, not as ground truth of the
  "true" probability.
- Clearly label any synthetic or simulated data.
- Retain simpler baselines and negative results.
- Explicitly audit for look-ahead bias: no feature may use information from
  after the point in question, such as a player's final match statistics
  leaking into an in-play feature.

## Source

Derived from `docs/CourtEdge_Architecture_and_Task_Definition.docx`, section 9.
