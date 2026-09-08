"""The learned meta-model (Journey 14): EXP34 — stacks the Markov and ML
outputs together with the raw features into one learned combiner, instead
of the fixed-formula weighted average (pricing/blend/blend.py, Journey
12). A stacking approach: a simple model (logistic regression, to avoid
the meta-learner itself overfitting) reads both base estimates plus the
score-state/context/momentum features, and can in principle learn things
a fixed weight can't — e.g. "trust Markov more in the deciding set".
"""

from __future__ import annotations

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

MARKOV_PREDICTION_COL = "markov_prediction"
ML_PREDICTION_COL = "ml_prediction"


def build_stacked_features(
    df: pd.DataFrame,
    markov_predictions: list[float],
    ml_predictions: list[float],
    base_feature_columns: list[str],
) -> tuple[pd.DataFrame, list[str]]:
    """Adds the two base estimates as columns and returns (stacked_df,
    the full column list to train/predict on)."""
    if len(markov_predictions) != len(df) or len(ml_predictions) != len(df):
        raise ValueError("markov_predictions and ml_predictions must match df's row count")
    stacked = df.copy()
    stacked[MARKOV_PREDICTION_COL] = markov_predictions
    stacked[ML_PREDICTION_COL] = ml_predictions
    stacked_columns = [MARKOV_PREDICTION_COL, ML_PREDICTION_COL] + base_feature_columns
    return stacked, stacked_columns


class MetaModel:
    """A thin wrapper so callers don't need to know it's logistic
    regression internally — consistent with how pricing/ml/train.py
    already wraps model_kind choices."""

    def __init__(self) -> None:
        self._model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
        self._feature_columns: list[str] | None = None

    def fit(self, stacked_df: pd.DataFrame, feature_columns: list[str], label_col: str = "label") -> "MetaModel":
        self._feature_columns = feature_columns
        self._model.fit(stacked_df[feature_columns], stacked_df[label_col])
        return self

    def predict(self, stacked_df: pd.DataFrame) -> list[float]:
        if self._feature_columns is None:
            raise RuntimeError("MetaModel must be fit() before predict()")
        return self._model.predict_proba(stacked_df[self._feature_columns])[:, 1].tolist()


def predict_with_fallback(
    meta_model: MetaModel,
    row: dict,
    feature_columns: list[str],
    markov_p: float | None,
    ml_p: float | None,
) -> tuple[float | None, bool]:
    """Returns (probability, fallback_used). The meta-model was trained
    expecting both base estimates present — it has no grounds to
    extrapolate sensibly if one is missing, so a missing ML estimate
    falls back to Markov-only (the same graceful-degradation shape as
    docs/architecture/deployment.md's fallback table), and a missing
    Markov estimate (which should never actually happen — it has no
    upstream dependency that fails independently) falls back to the ML
    estimate. Returns (None, True) only if both are missing — nothing to
    serve; the caller (trading_rules.apply_trading_rules) will suspend."""
    if ml_p is None and markov_p is None:
        return None, True
    if ml_p is None:
        return markov_p, True
    if markov_p is None:
        return ml_p, True

    stacked_row = {**row, MARKOV_PREDICTION_COL: markov_p, ML_PREDICTION_COL: ml_p}
    stacked_df = pd.DataFrame([stacked_row])
    prediction = meta_model.predict(stacked_df)[0]
    return prediction, False
