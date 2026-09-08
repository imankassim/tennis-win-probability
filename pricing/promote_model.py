"""Trains and persists the full pricing pipeline for live serving
(Journey 17): the ML model (EXP24's feature set), the phase-level
calibrator (EXP43), and the blend weight (EXP33) — bundled into one
versioned artefact backend/main.py loads at startup.

Deliberately NOT automatic: per docs/architecture/governance.md, model
promotion requires human review, so this is a script someone runs on
purpose, not something that fires on a schedule or a data change.
Running it is the review — the evidence behind these choices (the
feature set, the blend weight, the calibration method) already exists in
experiments/EXP20-24, EXP32-33 and EXP40-43; this script doesn't
re-derive them, it packages the already-decided configuration.

The ML model is trained on the older 85% of matches (chronologically);
the calibrator is fit on predictions for the newer 15% — held out from
the ML model's own training data, so calibration reflects genuinely
out-of-sample miscalibration rather than the model's fit to its own
training set.

Run it via pricing/run_promotion.py, not this module directly — see that
file's docstring for why the CLI entry point has to live in a separate
module from the PricingArtefacts class it pickles.

Usage:
    python -m pricing.run_promotion <matches.csv> <points1.csv> [<points2.csv> ...]
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import joblib
from lightgbm import LGBMClassifier

from database.ingestion.match_charting_project import parse_matches, parse_points_by_match
from database.ingestion.outcomes import derive_outcome
from database.models import Point, QuarantinedMatch
from pricing.blend.blend import blend_probability
from pricing.calibration.calibration import PhaseCalibrator, match_phase
from pricing.markov.engine import markov_probability
from pricing.markov.serve_rate import bulk_shrunk_serve_rates
from pricing.ml.features import build_point_features, compute_match_context_features
from pricing.ml.train import FEATURE_SETS, match_level_split

MODEL_VERSION = "blend_v1_calibrated"
BLEND_MARKOV_WEIGHT = 0.15  # EXP33's tuned weight
CALIBRATION_HOLDOUT_FRACTION = 0.15
# Reuses the model-artefacts location already reserved for this in
# .gitignore, alongside where the model card (Journey 17) lives.
DEFAULT_ARTEFACT_DIR = Path("docs/model_cards/artefacts")
ARTEFACT_FILENAME = "pricing_pipeline.joblib"


@dataclass(frozen=True)
class PricingArtefacts:
    model_version: str
    ml_model: LGBMClassifier
    calibrator: PhaseCalibrator
    blend_markov_weight: float
    feature_columns: list[str]
    trained_at: str
    n_training_matches: int
    n_calibration_matches: int


def _ingest(matches_csv: Path, points_csvs: list[Path]):
    parsed_matches, _ = parse_matches(matches_csv)
    matches = [m for m, _a, _b in parsed_matches]
    match_ids = {m.match_id for m in matches}
    matches_by_id = {m.match_id: m for m in matches}

    points_by_match: dict[str, list[Point]] = {}
    for points_csv in points_csvs:
        parsed_points, _ = parse_points_by_match(points_csv, match_ids)
        points_by_match.update(parsed_points)

    outcomes = {}
    for match_id, points in points_by_match.items():
        outcome = derive_outcome(matches_by_id[match_id], points)
        if not isinstance(outcome, QuarantinedMatch):
            outcomes[match_id] = outcome

    return matches, points_by_match, outcomes


def train_and_promote(matches_csv: Path, points_csvs: list[Path]) -> PricingArtefacts:
    matches, points_by_match, outcomes = _ingest(matches_csv, points_csvs)
    return _train_and_promote_from_data(matches, points_by_match, outcomes)


def _train_and_promote_from_data(matches, points_by_match, outcomes) -> PricingArtefacts:
    ctx = compute_match_context_features(matches, outcomes)
    df = build_point_features(matches, points_by_match, outcomes, ctx)
    feature_columns = FEATURE_SETS["state_context_momentum"]

    fit_df, calibration_df = match_level_split(df, test_fraction=CALIBRATION_HOLDOUT_FRACTION)

    ml_model = LGBMClassifier(n_estimators=100, max_depth=6, verbose=-1)
    ml_model.fit(fit_df[feature_columns], fit_df["label"])

    # Blend predictions on the calibration holdout, to fit the calibrator
    # against. bulk_shrunk_serve_rates computes every match's serve rates
    # in one archive pass — calling the per-match estimator once per row
    # here would re-scan the whole archive per point (already learned
    # that lesson once this session, see pricing/markov/serve_rate.py).
    serve_rates = bulk_shrunk_serve_rates(matches, points_by_match)
    ml_preds = ml_model.predict_proba(calibration_df[feature_columns])[:, 1].tolist()
    blend_preds = []
    phases = []
    for (_, row), ml_p in zip(calibration_df.iterrows(), ml_preds):
        p_a, p_b = serve_rates[row["match_id"]]
        server = "player_a" if row["server_is_a"] == 1 else "player_b"
        markov_p = markov_probability(
            p_a, p_b, row["best_of"], row["sets_a"], row["sets_b"],
            row["games_a"], row["games_b"], server,
        )
        blend_preds.append(blend_probability(markov_p, ml_p, BLEND_MARKOV_WEIGHT))
        phases.append(match_phase(row["sets_a"] + row["sets_b"] + 1, row["best_of"]))

    calibrator = PhaseCalibrator(min_samples_per_phase=500).fit(
        blend_preds, calibration_df["label"].tolist(), phases
    )

    return PricingArtefacts(
        model_version=MODEL_VERSION,
        ml_model=ml_model,
        calibrator=calibrator,
        blend_markov_weight=BLEND_MARKOV_WEIGHT,
        feature_columns=feature_columns,
        trained_at=datetime.now(timezone.utc).isoformat(),
        n_training_matches=fit_df["match_id"].nunique(),
        n_calibration_matches=calibration_df["match_id"].nunique(),
    )


def save_artefacts(artefacts: PricingArtefacts, directory: Path = DEFAULT_ARTEFACT_DIR) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    joblib.dump(artefacts, directory / ARTEFACT_FILENAME)
