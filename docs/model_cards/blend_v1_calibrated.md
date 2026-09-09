# Model card: blend_v1_calibrated

The pipeline `pricing/promote_model.py` packages and `backend/probability.py`
serves under `model_version="blend_v1_calibrated"` — the format follows the
standard "model details / intended use / training data / evaluation /
caveats" model-card shape, filled in with this project's real evidence
rather than placeholders. See [pricing/README.md](../../pricing/README.md)
for how to reproduce it and [docs/ROADMAP.md](../ROADMAP.md) for how it fits
into the overall build.

## Model details

- **What it is**: three components computed independently, then combined —
  a point-to-match Markov chain (analytic, EXP9-13), a LightGBM classifier
  (learned, EXP24), a validation-tuned weighted blend of the two (EXP33),
  and a per-match-phase isotonic calibrator (EXP43).
- **Owner / date**: this repository, built 2026-09-08/09.
- **Type**: binary probability estimator — P(player A wins the match) at
  a given in-match score state.
- **Not a single model**: "blend_v1_calibrated" names the whole promoted
  bundle (`pricing.promote_model.PricingArtefacts`), not one classifier.
  The Markov component has no learned parameters to version; only the
  LightGBM model and the calibrator are fit from data.

## Intended use

- **Intended**: an in-play win-probability research prototype — replaying
  historical matches point by point and comparing this system's
  probabilities/prices against Markov-only and against the de-vigged
  market (EXP15), for a portfolio/research demonstration.
- **Explicitly not intended**: real-money trading, betting advice, or a
  staking recommendation of any kind (see
  [docs/architecture/governance.md](../architecture/governance.md)'s
  "Responsible framing" and the root [README.md](../../README.md)'s
  "Prototype boundary"). Never presented as such anywhere in this
  codebase's own output.

## Training data

Match Charting Project (decision 9) point-by-point charts, 2010s+2020s
files: 5,457 matches / 891,514 points with a confirmed outcome (115
correctly quarantined as incomplete, 36 malformed source rows skipped —
see [database/README.md](../../database/README.md)). No player-identifying
information beyond the player names already public in the source data;
no financial or real-user data of any kind.

`pricing/promote_model.py`'s split (chronological, match-level, never
point-level — see
[docs/architecture/offline-training-architecture.md](../architecture/offline-training-architecture.md)):

| Slice | Matches | Role |
|---|---|---|
| Training | 4,639 (oldest 85%) | Fits the LightGBM model |
| Calibration | 409 (next ~7.5%) | Fits the phase calibrator on the trained model's blended predictions |
| Quality evaluation | ~409 (newest ~7.5%) | Scores the finished pipeline — neither the model nor the calibrator was fit on this slice |

## Feature schema

`pricing/ml/features.py`'s `STATE_FEATURES` + `CONTEXT_FEATURES` +
`MOMENTUM_FEATURES` (EXP24's leading feature set) — 14 columns, computed
identically for training (`build_point_features`) and live serving
(`backend/probability.py`'s `build_feature_row`, checked for exact parity
by `tests/unit/test_feature_sync.py`):

| Feature | Type | Range / default | Source |
|---|---|---|---|
| `best_of` | int | 3 or 5 | Match metadata |
| `sets_a`, `sets_b` | int | 0-2 (best of 3) / 0-3 (best of 5) | Current score state |
| `games_a`, `games_b` | int | 0-7+ | Current score state |
| `server_is_a` | int (0/1) | — | Current score state |
| `momentum_a` | float | [0, 1], default 0.5 | Fraction of the last 10 points (this match only) won by player A |
| `form_a`, `form_b` | float | [0, 1], default 0.5 | Win rate over each player's last 10 completed matches before this one |
| `surface_rate_a`, `surface_rate_b` | float | [0, 1], default 0.5 | Each player's win rate on this match's surface, before this match |
| `h2h_rate_a` | float | [0, 1], default 0.5 | Player A's win rate in this exact pairing's prior meetings |
| `elo_a`, `elo_b` | float | default 1500.0 | Self-computed Elo (`backend/player_rating.py`; no external ranking feed exists) |

All context features carry a strict no-look-ahead guarantee (a feature
for match *N* never sees match *N*'s own result or any later match's) —
enforced by construction in `compute_match_context_features`, not by a
post-hoc filter.

The Markov component's own inputs (not part of the table above, since
they feed the analytic estimate, not the ML model) are each player's
serve-win rate, Bayesian-shrunk toward the tour average
(`pricing/markov/serve_rate.py`, EXP13, shrinkage strength 20, cold-start
0.6 for a player with zero prior history).

## Evaluation

Every number below is real, from this project's own experiments — see
[experiments/REGISTER.md](../../experiments/REGISTER.md) for the full
catalogue and [evaluation/FINAL_EVALUATION.md](../../evaluation/FINAL_EVALUATION.md)
for the synthesised comparison.

| Configuration | Brier score | Log-loss | Source |
|---|---|---|---|
| EXP1 — always 50/50 | 0.2500 | 0.6931 | Floor |
| EXP2 — score-leader heuristic | 0.1934 | 0.5737 | Primitive baseline |
| Markov (serve rates, shrunk) | 0.1839 | 0.5579 | Analytic baseline |
| ML alone (EXP24) | ~0.1500 (held-out test) | ~0.4540 | Learned candidate |
| Blend (EXP33) | ~0.1490 (held-out test) | ~0.4525 | Combined estimate |
| **blend_v1_calibrated, quality-eval slice** | **0.1481** | **0.4648** | This promoted pipeline, genuinely out-of-sample |
| De-vigged market (EXP15, pre-match only) | 0.1828 | 0.5418 | External comparator — beats this system pre-match |

Calibration (ECE, lower is better): 0.0252 on this pipeline's
quality-eval slice — in the same range as EXP43's reported 0.0113 on a
differently-sized held-out split (see
[pricing/README.md](../../pricing/README.md) for why the two numbers
aren't directly comparable, only similarly small).

**Cross-era check (EXP44)**: scored across the archive's 2010s vs 2020s
halves, Brier 0.1183 vs 0.1312 — no collapse, but a real ~11% relative
gap, confounded with the promotion script's recency-based (not
era-based) split. See
[experiments/EXP44-cross-era-drift.md](../../experiments/EXP44-cross-era-drift.md).

## Caveats and recommendations

- **The de-vigged market beats this system pre-match** (EXP15) — expected
  and reported as the honest result, not a "beat the market" claim. This
  system has no access to injury news, insider form, or line movement;
  its edge is entirely in-play score-state and archive-derived context.
- **The cross-era comparison (EXP44) is not a clean drift test** — see
  its write-up for the exact confound. Treat the ~11% Brier gap as a
  flag worth further investigation, not a confirmed generalisation
  failure.
- **A learned meta-model was tried and rejected** (EXP34) — the simple
  tuned blend (EXP33) beats a stacked combiner here, diagnosed as
  overfitting given the real sample size (4,363 independent matches
  behind many more point-rows).
- **Not licensed or reviewed for real-money use** — see "Intended use"
  above and [docs/ethics/assessment.md](../ethics/assessment.md).
