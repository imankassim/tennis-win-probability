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
the newest 15% is split again in half by date, fitting the calibrator on
the earlier half and reporting quality metrics (calibration_brier/
_log_loss/_ece, surfaced by Journey 19's ops dashboard) on the later
half. A genuine three-way split, not two: scoring the calibrator on the
same data it was fit on would report near-perfect calibration by
construction (isotonic regression fits its own training data closely),
not a real out-of-sample estimate — the same reasoning EXP40-43's
validation-half / final-test-half split already used, applied here too.

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
from evaluation.metrics import brier_score, expected_calibration_error, log_loss
from pricing.blend.blend import blend_probability
from pricing.calibration.calibration import PhaseCalibrator, match_phase
from pricing.markov.engine import markov_probability
from pricing.markov.serve_rate import bulk_shrunk_serve_rates
from pricing.ml.features import build_point_features, compute_match_context_features
from pricing.ml.train import FEATURE_SETS, match_level_split
from pricing.registry import RegistryEntry, add_entry

MODEL_VERSION = "blend_v1_calibrated"
BLEND_MARKOV_WEIGHT = 0.15  # EXP33's tuned weight
CALIBRATION_HOLDOUT_FRACTION = 0.15
# Reuses the model-artefacts location already reserved for this in
# .gitignore, alongside where the model card (Journey 17) lives.
DEFAULT_ARTEFACT_DIR = Path("docs/model_cards/artefacts")
ARTEFACT_FILENAME = "pricing_pipeline.joblib"
VERSIONS_SUBDIR = "versions"


@dataclass(frozen=True)
class PricingArtefacts:
    # A filesystem-safe id for this promotion (Journey 20's model
    # registry) — distinct from trained_at (a full ISO timestamp, kept
    # for display) because ISO timestamps contain colons, which several
    # filesystems (including the one this project actually runs on)
    # reject in filenames.
    version: str
    model_version: str
    ml_model: LGBMClassifier
    calibrator: PhaseCalibrator
    blend_markov_weight: float
    feature_columns: list[str]
    trained_at: str
    n_training_matches: int
    # Matches the calibrator was FIT on — half of the 15% holdout; the
    # other half (never seen by the calibrator) produced calibration_brier
    # /_log_loss/_ece below, so this count and those metrics deliberately
    # come from two different, disjoint slices.
    n_calibration_matches: int
    # The calibrated pipeline's accuracy/calibration on a slice neither
    # the ML model nor the calibrator was fit on, at promotion time — a
    # genuine out-of-sample "quality" snapshot (Journey 19's ops
    # dashboard surfaces these), computed the same way EXP40-43 were
    # evaluated (a validation half fits, a separate final-test half
    # scores). Not a live metric — this system has no live feed of
    # outcomes to score served quotes against (see
    # docs/architecture/charter.md's "what will not be built").
    calibration_brier: float
    calibration_log_loss: float
    calibration_ece: float


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


def _blend_predictions_and_phases(
    df,
    ml_model: LGBMClassifier,
    feature_columns: list[str],
    serve_rates: dict[str, tuple[float, float]],
) -> tuple[list[float], list[str]]:
    """Markov + ML computed independently, then blended, for every row of
    `df` — the same computation the live API performs per-request, run
    here in bulk. bulk_shrunk_serve_rates (passed in, computed once for
    the whole archive) avoids re-scanning it per match — already learned
    that lesson once this session, see pricing/markov/serve_rate.py."""
    ml_preds = ml_model.predict_proba(df[feature_columns])[:, 1].tolist()
    blend_preds = []
    phases = []
    for (_, row), ml_p in zip(df.iterrows(), ml_preds):
        p_a, p_b = serve_rates[row["match_id"]]
        server = "player_a" if row["server_is_a"] == 1 else "player_b"
        markov_p = markov_probability(
            p_a, p_b, row["best_of"], row["sets_a"], row["sets_b"],
            row["games_a"], row["games_b"], server,
        )
        blend_preds.append(blend_probability(markov_p, ml_p, BLEND_MARKOV_WEIGHT))
        phases.append(match_phase(row["sets_a"] + row["sets_b"] + 1, row["best_of"]))
    return blend_preds, phases


def _train_and_promote_from_data(matches, points_by_match, outcomes) -> PricingArtefacts:
    ctx = compute_match_context_features(matches, outcomes)
    df = build_point_features(matches, points_by_match, outcomes, ctx)
    feature_columns = FEATURE_SETS["state_context_momentum"]

    fit_df, holdout_df = match_level_split(df, test_fraction=CALIBRATION_HOLDOUT_FRACTION)
    # The 15% holdout splits again, in half by date: the calibrator fits
    # on the earlier half and reports quality on the later half — never
    # scored on its own fitting data (see this module's docstring).
    calibration_fit_df, quality_eval_df = match_level_split(holdout_df, test_fraction=0.5)

    ml_model = LGBMClassifier(n_estimators=100, max_depth=6, verbose=-1)
    ml_model.fit(fit_df[feature_columns], fit_df["label"])

    serve_rates = bulk_shrunk_serve_rates(matches, points_by_match)

    calibration_preds, calibration_phases = _blend_predictions_and_phases(
        calibration_fit_df, ml_model, feature_columns, serve_rates
    )
    calibrator = PhaseCalibrator(min_samples_per_phase=500).fit(
        calibration_preds, calibration_fit_df["label"].tolist(), calibration_phases
    )

    quality_preds, quality_phases = _blend_predictions_and_phases(
        quality_eval_df, ml_model, feature_columns, serve_rates
    )
    calibrated_quality_preds = calibrator.predict(quality_preds, quality_phases)
    quality_labels = quality_eval_df["label"].tolist()

    now = datetime.now(timezone.utc)
    return PricingArtefacts(
        version=now.strftime("%Y%m%dT%H%M%SZ"),
        model_version=MODEL_VERSION,
        ml_model=ml_model,
        calibrator=calibrator,
        blend_markov_weight=BLEND_MARKOV_WEIGHT,
        feature_columns=feature_columns,
        trained_at=now.isoformat(),
        n_training_matches=fit_df["match_id"].nunique(),
        n_calibration_matches=calibration_fit_df["match_id"].nunique(),
        calibration_brier=brier_score(calibrated_quality_preds, quality_labels),
        calibration_log_loss=log_loss(calibrated_quality_preds, quality_labels),
        calibration_ece=expected_calibration_error(calibrated_quality_preds, quality_labels),
    )


def save_artefacts(artefacts: PricingArtefacts, directory: Path = DEFAULT_ARTEFACT_DIR) -> None:
    """Writes the versioned artefact (kept permanently, for rollback —
    see pricing/registry.py and pricing/rollback_model.py), makes it the
    active one (the fixed filename backend/probability.py's
    load_artefacts reads), and records the promotion in the registry."""
    directory.mkdir(parents=True, exist_ok=True)
    versions_dir = directory / VERSIONS_SUBDIR
    versions_dir.mkdir(parents=True, exist_ok=True)

    versioned_path = versions_dir / f"pricing_pipeline_{artefacts.version}.joblib"
    joblib.dump(artefacts, versioned_path)
    joblib.dump(artefacts, directory / ARTEFACT_FILENAME)

    add_entry(
        directory,
        RegistryEntry(
            version=artefacts.version,
            model_version=artefacts.model_version,
            trained_at=artefacts.trained_at,
            n_training_matches=artefacts.n_training_matches,
            n_calibration_matches=artefacts.n_calibration_matches,
            calibration_brier=artefacts.calibration_brier,
            calibration_log_loss=artefacts.calibration_log_loss,
            calibration_ece=artefacts.calibration_ece,
            active=True,
        ),
    )
