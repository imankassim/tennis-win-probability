from datetime import date, timedelta

import pandas as pd
import pytest

from pricing.ml.train import match_level_split, train_and_evaluate


def _synthetic_dataset(n_matches=20, points_per_match=10, seed=0):
    """A small, deterministic dataset where the label is strongly
    predictable from `sets_a` alone, so a fitted model should score
    clearly better than chance — a sanity check on the training
    machinery, not a claim about real accuracy."""
    import random

    rng = random.Random(seed)
    rows = []
    base_date = date(2026, 1, 1)
    for m in range(n_matches):
        match_id = f"m{m}"
        match_date = base_date + timedelta(days=m)
        # Label correlates with a fixed per-match "skill" value.
        skill = rng.random()
        label = 1 if skill > 0.5 else 0
        for p in range(points_per_match):
            rows.append(
                {
                    "match_id": match_id,
                    "point_no": p + 1,
                    "match_date": match_date,
                    "label": label,
                    "best_of": 3,
                    "sets_a": round(skill * 2),
                    "sets_b": round((1 - skill) * 2),
                    "games_a": p,
                    "games_b": points_per_match - p,
                    "server_is_a": p % 2,
                    "momentum_a": skill,
                }
            )
    return pd.DataFrame(rows)


def test_match_level_split_never_splits_a_match_across_sides():
    df = _synthetic_dataset()
    train_df, test_df = match_level_split(df, test_fraction=0.2)
    assert set(train_df["match_id"]) & set(test_df["match_id"]) == set()


def test_match_level_split_holds_out_the_most_recent_matches():
    df = _synthetic_dataset(n_matches=10)
    train_df, test_df = match_level_split(df, test_fraction=0.2)
    assert train_df["match_date"].max() < test_df["match_date"].min()


def test_match_level_split_respects_test_fraction_at_match_level():
    df = _synthetic_dataset(n_matches=20)
    train_df, test_df = match_level_split(df, test_fraction=0.2)
    assert test_df["match_id"].nunique() == 4  # 20% of 20 matches
    assert train_df["match_id"].nunique() == 16


@pytest.mark.parametrize("model_kind", ["logistic", "lightgbm"])
def test_train_and_evaluate_beats_chance_on_a_learnable_dataset(model_kind):
    df = _synthetic_dataset(n_matches=60)
    train_df, test_df = match_level_split(df, test_fraction=0.3)

    result = train_and_evaluate(
        "test", model_kind, ["sets_a", "sets_b", "momentum_a"], train_df, test_df
    )
    assert result.brier < 0.25  # clearly better than always-50/50
    assert result.n_train_matches + result.n_test_matches == 60
    assert result.n_test_points > 0
