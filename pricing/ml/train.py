"""Trains and evaluates EXP20-24: logistic regression and LightGBM over
increasing feature sets, on a match-level train/test split.

Match-level, never point-level (docs/architecture/offline-training-architecture.md's
training controls: "a model that has seen the middle of a match must never
have seen its ending"). The split is chronological — the most recent
matches held out as the test set — rather than a random match-level split,
closer to the documented control ("hold out an entire final set of
tournaments as the test set") than a shuffled split would be, and it means
no test-set match's outcome could possibly have informed feature
construction for an earlier training-set match either.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.linear_model import LogisticRegression

from evaluation.metrics import brier_score, log_loss
from pricing.ml.features import CONTEXT_FEATURES, MOMENTUM_FEATURES, STATE_FEATURES

FEATURE_SETS: dict[str, list[str]] = {
    "state_only": STATE_FEATURES,
    "state_context": STATE_FEATURES + CONTEXT_FEATURES,
    "state_context_momentum": STATE_FEATURES + CONTEXT_FEATURES + MOMENTUM_FEATURES,
}


@dataclass(frozen=True)
class MlEvaluationResult:
    configuration: str
    n_train_points: int
    n_test_points: int
    n_train_matches: int
    n_test_matches: int
    brier: float
    log_loss: float


def match_level_split(
    df: pd.DataFrame, test_fraction: float = 0.2
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Splits by match_id, ordered by match_date — the most recent
    `test_fraction` of matches become the test set. Never splits a single
    match's points across both sides."""
    match_dates = df.groupby("match_id")["match_date"].first().sort_values()
    n_test = max(1, int(len(match_dates) * test_fraction))
    test_match_ids = set(match_dates.index[-n_test:])
    train_match_ids = set(match_dates.index[:-n_test])

    train_df = df[df["match_id"].isin(train_match_ids)]
    test_df = df[df["match_id"].isin(test_match_ids)]
    return train_df, test_df


def train_and_evaluate(
    configuration_name: str,
    model_kind: str,
    feature_columns: list[str],
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
) -> MlEvaluationResult:
    """model_kind: 'logistic' or 'lightgbm'."""
    x_train = train_df[feature_columns]
    y_train = train_df["label"]
    x_test = test_df[feature_columns]
    y_test = test_df["label"].tolist()

    if model_kind == "logistic":
        model = LogisticRegression(max_iter=1000)
    elif model_kind == "lightgbm":
        model = LGBMClassifier(n_estimators=100, max_depth=6, verbose=-1)
    else:
        raise ValueError(f"unknown model_kind: {model_kind!r}")

    model.fit(x_train, y_train)
    predictions = model.predict_proba(x_test)[:, 1].tolist()

    return MlEvaluationResult(
        configuration=configuration_name,
        n_train_points=len(train_df),
        n_test_points=len(test_df),
        n_train_matches=train_df["match_id"].nunique(),
        n_test_matches=test_df["match_id"].nunique(),
        brier=brier_score(predictions, y_test),
        log_loss=log_loss(predictions, y_test),
    )
