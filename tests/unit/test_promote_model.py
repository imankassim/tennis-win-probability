from dataclasses import replace
from datetime import date, timedelta

import joblib

from database.models import Match, OutcomeLabel, Point
from pricing.ml.train import FEATURE_SETS
from pricing.promote_model import (
    BLEND_MARKOV_WEIGHT,
    MODEL_VERSION,
    PricingArtefacts,
    _train_and_promote_from_data,
    save_artefacts,
)
from pricing.registry import load_registry

# Two-player pool alternating roles across matches so both sides of every
# match_id have real prior serve/context history to draw on (matches
# EXP20-24's "no debut-only synthetic archive" shape).
PLAYERS = ["p1", "p2", "p3", "p4"]


def _synthetic_archive(n_matches=100, points_per_match=20, seed=0):
    """A small, deterministic archive with a real per-match progression
    (not just 1-2 points), so context features, momentum and serve rates
    all have something real to compute from. Mirrors the shape of
    tests/unit/test_ml_features.py's helpers, scaled up for a full
    promote-and-calibrate run."""
    import random

    rng = random.Random(seed)
    base_date = date(2024, 1, 1)

    matches: list[Match] = []
    outcomes: dict[str, OutcomeLabel] = {}
    points_by_match: dict[str, list[Point]] = {}

    for m in range(n_matches):
        match_id = f"m{m}"
        a, b = rng.sample(PLAYERS, 2)
        match_date = base_date + timedelta(days=m)
        matches.append(
            Match(
                match_id=match_id,
                tournament="t",
                round="F",
                surface="hard",
                best_of=3,
                match_date=match_date,
                player_a_id=a,
                player_b_id=b,
                source="test",
            )
        )
        a_wins = rng.random() > 0.5
        winner = "player_a" if a_wins else "player_b"
        outcomes[match_id] = OutcomeLabel(
            match_id=match_id, actual_winner=winner, final_score="2-0"
        )

        pts = []
        sets_a = sets_b = games_a = games_b = 0
        for p in range(points_per_match):
            server = "player_a" if p % 2 == 0 else "player_b"
            point_winner = winner if rng.random() < 0.7 else (
                "player_b" if winner == "player_a" else "player_a"
            )
            pts.append(
                Point(
                    match_id=match_id,
                    point_no=p + 1,
                    set_no=1,
                    game_no=1,
                    server=server,
                    point_winner=point_winner,
                    sets_won_a=sets_a,
                    sets_won_b=sets_b,
                    games_won_a=games_a,
                    games_won_b=games_b,
                    point_score="n/a",
                )
            )
            if p % 4 == 3:
                if a_wins:
                    games_a += 1
                else:
                    games_b += 1
        points_by_match[match_id] = pts

    return matches, points_by_match, outcomes


def test_train_and_promote_produces_a_complete_artefact_bundle():
    matches, points_by_match, outcomes = _synthetic_archive()
    artefacts = _train_and_promote_from_data(matches, points_by_match, outcomes)

    assert isinstance(artefacts, PricingArtefacts)
    assert artefacts.version
    assert artefacts.model_version == MODEL_VERSION
    assert artefacts.blend_markov_weight == BLEND_MARKOV_WEIGHT
    assert artefacts.feature_columns == FEATURE_SETS["state_context_momentum"]
    # n_calibration_matches only counts the half of the 15% holdout the
    # calibrator was actually fit on - the other half (never fit on by
    # anything) produced calibration_brier/_log_loss/_ece, so the two
    # numbers deliberately don't sum to the full archive size.
    assert artefacts.n_training_matches < 100
    assert artefacts.n_calibration_matches >= 1
    assert 0.0 <= artefacts.calibration_brier <= 1.0
    assert artefacts.calibration_log_loss >= 0.0
    assert 0.0 <= artefacts.calibration_ece <= 1.0


def test_promoted_model_predicts_probabilities_in_range():
    matches, points_by_match, outcomes = _synthetic_archive()
    artefacts = _train_and_promote_from_data(matches, points_by_match, outcomes)

    # Exercise the ml model directly with a zeroed feature row of the
    # right shape rather than hand-building a realistic one - this test
    # only checks the artefact is a usable, well-formed predictor.
    import pandas as pd

    row = pd.DataFrame([{col: 0.0 for col in artefacts.feature_columns}])
    proba = artefacts.ml_model.predict_proba(row)[:, 1][0]
    assert 0.0 <= proba <= 1.0

    calibrated = artefacts.calibrator.predict([proba], ["early"])
    assert 0.0 <= calibrated[0] <= 1.0


def test_save_and_load_artefacts_round_trips(tmp_path):
    matches, points_by_match, outcomes = _synthetic_archive()
    artefacts = _train_and_promote_from_data(matches, points_by_match, outcomes)

    save_artefacts(artefacts, directory=tmp_path)
    loaded = joblib.load(tmp_path / "pricing_pipeline.joblib")

    assert loaded.model_version == artefacts.model_version
    assert loaded.feature_columns == artefacts.feature_columns
    assert loaded.trained_at == artefacts.trained_at


def test_save_artefacts_keeps_a_versioned_copy_and_registers_it(tmp_path):
    matches, points_by_match, outcomes = _synthetic_archive()
    artefacts = _train_and_promote_from_data(matches, points_by_match, outcomes)

    save_artefacts(artefacts, directory=tmp_path)

    versioned_path = tmp_path / "versions" / f"pricing_pipeline_{artefacts.version}.joblib"
    assert versioned_path.exists()
    assert joblib.load(versioned_path).version == artefacts.version

    entries = load_registry(tmp_path)
    assert len(entries) == 1
    assert entries[0].version == artefacts.version
    assert entries[0].active is True


def test_save_artefacts_twice_keeps_both_versions_with_only_the_newest_active(tmp_path):
    matches, points_by_match, outcomes = _synthetic_archive()
    artefacts = _train_and_promote_from_data(matches, points_by_match, outcomes)

    first = replace(artefacts, version="v1")
    second = replace(artefacts, version="v2")
    save_artefacts(first, directory=tmp_path)
    save_artefacts(second, directory=tmp_path)

    assert (tmp_path / "versions" / "pricing_pipeline_v1.joblib").exists()
    assert (tmp_path / "versions" / "pricing_pipeline_v2.joblib").exists()
    # The fixed active filename always reflects the most recently saved version.
    assert joblib.load(tmp_path / "pricing_pipeline.joblib").version == "v2"

    entries = {e.version: e for e in load_registry(tmp_path)}
    assert entries["v1"].active is False
    assert entries["v2"].active is True
