from datetime import date, timedelta

import numpy as np

from database.models import Match, OutcomeLabel, Point
from evaluation.drift_check import era_metrics, score_full_pipeline, split_by_era
from pricing.ml.train import FEATURE_SETS
from pricing.promote_model import PricingArtefacts

PLAYERS = ["p1", "p2", "p3", "p4"]
SPLIT_DATE = date(2024, 7, 1)  # midpoint of the synthetic archive's ~360-day span


class _ConstantModel:
    """Always predicts 0.6 for player_a — a fake standing in for LightGBM
    so this test exercises score_full_pipeline's wiring, not a real
    model's accuracy."""

    def predict_proba(self, x):
        n = len(x)
        return np.column_stack([np.full(n, 0.4), np.full(n, 0.6)])


class _PassthroughCalibrator:
    def predict(self, predictions, phases):
        return list(predictions)


def _artefacts() -> PricingArtefacts:
    return PricingArtefacts(
        version="20260101T000000Z",
        model_version="blend_v1_calibrated",
        ml_model=_ConstantModel(),
        calibrator=_PassthroughCalibrator(),
        blend_markov_weight=0.15,
        feature_columns=FEATURE_SETS["state_context_momentum"],
        trained_at="2026-01-01T00:00:00+00:00",
        n_training_matches=1,
        n_calibration_matches=1,
        calibration_brier=0.2,
        calibration_log_loss=0.5,
        calibration_ece=0.05,
    )


def _archive(n_matches=10, points_per_match=6, seed=0):
    import random

    rng = random.Random(seed)
    base = date(2024, 1, 1)  # spans across SPLIT_DATE as n_matches grows
    matches, outcomes, points_by_match = [], {}, {}

    for m in range(n_matches):
        match_id = f"m{m}"
        a, b = rng.sample(PLAYERS, 2)
        match_date = base + timedelta(days=m * 40)  # ~13 months over 10 matches
        matches.append(
            Match(
                match_id=match_id, tournament="t", round="F", surface="hard", best_of=3,
                match_date=match_date, player_a_id=a, player_b_id=b, source="test",
            )
        )
        a_wins = rng.random() > 0.5
        outcomes[match_id] = OutcomeLabel(
            match_id=match_id, actual_winner="player_a" if a_wins else "player_b", final_score="2-0"
        )
        points_by_match[match_id] = [
            Point(
                match_id=match_id, point_no=p + 1, set_no=1, game_no=1,
                server="player_a" if p % 2 == 0 else "player_b",
                point_winner="player_a" if a_wins else "player_b",
                sets_won_a=0, sets_won_b=0, games_won_a=0, games_won_b=0, point_score="n/a",
            )
            for p in range(points_per_match)
        ]
    return matches, points_by_match, outcomes


def test_score_full_pipeline_produces_one_calibrated_row_per_point():
    matches, points_by_match, outcomes = _archive()
    scored = score_full_pipeline(_artefacts(), matches, points_by_match, outcomes)
    assert len(scored) == sum(len(pts) for pts in points_by_match.values())
    assert "calibrated_prediction" in scored.columns
    assert scored["calibrated_prediction"].between(0, 1).all()


def test_era_metrics_reports_correct_counts():
    matches, points_by_match, outcomes = _archive()
    scored = score_full_pipeline(_artefacts(), matches, points_by_match, outcomes)
    metrics = era_metrics(scored, "all")
    assert metrics.n_matches == len(matches)
    assert metrics.n_points == len(scored)
    assert metrics.brier >= 0
    assert metrics.log_loss >= 0
    assert metrics.ece >= 0


def test_split_by_era_partitions_every_point_exactly_once():
    matches, points_by_match, outcomes = _archive()
    scored = score_full_pipeline(_artefacts(), matches, points_by_match, outcomes)
    before, on_or_after = split_by_era(scored, SPLIT_DATE, "before", "on_or_after")
    assert before.n_points + on_or_after.n_points == len(scored)
    assert before.n_matches + on_or_after.n_matches == len(matches)
    # The synthetic archive spans well past SPLIT_DATE, so both eras are non-empty.
    assert before.n_points > 0
    assert on_or_after.n_points > 0
