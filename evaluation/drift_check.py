"""Cross-era drift check (Journey 18, EXP44): does the SAME promoted
pipeline's accuracy and calibration hold up evenly across chronologically
distinct eras of the archive, or has it quietly overfit to one of them?

The risk register (docs/architecture/risk_register.md) names this
directly: "overfitting to a particular rule or equipment era... evaluate
across multiple years and surfaces; monitor drift." This module makes
that concrete and measured rather than only asserted - it scores the
promoted pipeline (unmodified, not refit) against the whole archive once,
using the same no-look-ahead serve-rate and context-feature machinery
live serving uses, then buckets the results by era for comparison.

Deliberately scores the FULL archive in one pass rather than splitting it
into two archives and scoring each separately: bulk_shrunk_serve_rates
and compute_match_context_features build running per-player history in
date order, so scoring a later era in isolation would lose all the
earlier era's history - not what live serving actually sees. Bucketing
happens only after scoring, on match_date.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd

from database.models import Match, OutcomeLabel, Point
from evaluation.metrics import brier_score, expected_calibration_error, log_loss
from pricing.blend.blend import blend_probability
from pricing.calibration.calibration import match_phase
from pricing.markov.engine import markov_probability
from pricing.markov.serve_rate import bulk_shrunk_serve_rates
from pricing.ml.features import build_point_features, compute_match_context_features
from pricing.promote_model import PricingArtefacts


@dataclass(frozen=True)
class EraMetrics:
    era_label: str
    n_points: int
    n_matches: int
    brier: float
    log_loss: float
    ece: float


def score_full_pipeline(
    artefacts: PricingArtefacts,
    matches: list[Match],
    points_by_match: dict[str, list[Point]],
    outcomes: dict[str, OutcomeLabel],
) -> pd.DataFrame:
    """Scores the promoted pipeline's calibrated probability at every
    point of every match with a confirmed outcome. Same computation
    pricing/promote_model.py runs to fit the calibrator against a
    held-out slice - here it scores (never fits) against whatever
    archive is passed in, so the same promoted model/calibrator can be
    checked against a different or wider slice than it was promoted on."""
    ctx = compute_match_context_features(matches, outcomes)
    df = build_point_features(matches, points_by_match, outcomes, ctx)
    serve_rates = bulk_shrunk_serve_rates(matches, points_by_match)

    ml_preds = artefacts.ml_model.predict_proba(df[artefacts.feature_columns])[:, 1].tolist()
    blend_preds = []
    phases = []
    for (_, row), ml_p in zip(df.iterrows(), ml_preds):
        p_a, p_b = serve_rates[row["match_id"]]
        server = "player_a" if row["server_is_a"] == 1 else "player_b"
        markov_p = markov_probability(
            p_a,
            p_b,
            row["best_of"],
            row["sets_a"],
            row["sets_b"],
            row["games_a"],
            row["games_b"],
            server,
        )
        blend_preds.append(blend_probability(markov_p, ml_p, artefacts.blend_markov_weight))
        phases.append(match_phase(row["sets_a"] + row["sets_b"] + 1, row["best_of"]))

    scored = df.copy()
    scored["calibrated_prediction"] = artefacts.calibrator.predict(blend_preds, phases)
    return scored


def era_metrics(scored_df: pd.DataFrame, era_label: str) -> EraMetrics:
    predictions = scored_df["calibrated_prediction"].tolist()
    outcomes = scored_df["label"].tolist()
    return EraMetrics(
        era_label=era_label,
        n_points=len(scored_df),
        n_matches=scored_df["match_id"].nunique(),
        brier=brier_score(predictions, outcomes),
        log_loss=log_loss(predictions, outcomes),
        ece=expected_calibration_error(predictions, outcomes),
    )


def split_by_era(
    scored_df: pd.DataFrame, split_date: date, before_label: str, on_or_after_label: str
) -> tuple[EraMetrics, EraMetrics]:
    """Buckets an already-scored dataframe (from score_full_pipeline) into
    two eras by match_date and scores each independently. The split
    happens after scoring, not before - see this module's docstring for
    why scoring the eras separately would be wrong."""
    before = scored_df[scored_df["match_date"] < split_date]
    on_or_after = scored_df[scored_df["match_date"] >= split_date]
    return era_metrics(before, before_label), era_metrics(on_or_after, on_or_after_label)
