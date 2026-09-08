import random

import pandas as pd
import pytest

from pricing.blend.meta_model import (
    ML_PREDICTION_COL,
    MARKOV_PREDICTION_COL,
    MetaModel,
    build_stacked_features,
    predict_with_fallback,
)


def _synthetic_stacked_dataset(n=500, seed=0):
    """Label is determined by ml_prediction (a strong signal); markov and
    a noise feature are irrelevant — a well-fit meta-model should learn
    to lean on ml_prediction."""
    rng = random.Random(seed)
    rows = []
    for _ in range(n):
        ml_p = rng.random()
        markov_p = rng.random()  # uncorrelated with the label
        noise = rng.random()
        label = 1 if ml_p > 0.5 else 0
        rows.append(
            {
                MARKOV_PREDICTION_COL: markov_p,
                ML_PREDICTION_COL: ml_p,
                "noise": noise,
                "label": label,
            }
        )
    return pd.DataFrame(rows)


def test_build_stacked_features_adds_both_prediction_columns():
    df = pd.DataFrame({"label": [1, 0], "x": [1.0, 2.0]})
    stacked, columns = build_stacked_features(df, [0.6, 0.4], [0.7, 0.3], ["x"])
    assert list(stacked[MARKOV_PREDICTION_COL]) == [0.6, 0.4]
    assert list(stacked[ML_PREDICTION_COL]) == [0.7, 0.3]
    assert set(columns) == {MARKOV_PREDICTION_COL, ML_PREDICTION_COL, "x"}


def test_build_stacked_features_rejects_mismatched_lengths():
    df = pd.DataFrame({"label": [1, 0]})
    with pytest.raises(ValueError):
        build_stacked_features(df, [0.5], [0.5, 0.5], [])


def test_meta_model_learns_to_use_the_informative_feature():
    df = _synthetic_stacked_dataset(n=800)
    train_df, test_df = df.iloc[:600], df.iloc[600:]
    feature_columns = [MARKOV_PREDICTION_COL, ML_PREDICTION_COL, "noise"]

    model = MetaModel().fit(train_df, feature_columns)
    predictions = model.predict(test_df)

    from evaluation.metrics import brier_score

    assert brier_score(predictions, test_df["label"].tolist()) < 0.15


def test_meta_model_raises_if_predict_called_before_fit():
    with pytest.raises(RuntimeError):
        MetaModel().predict(pd.DataFrame({"x": [1]}))


class TestPredictWithFallback:
    def _fitted_model(self):
        df = _synthetic_stacked_dataset(n=200)
        return MetaModel().fit(df, [MARKOV_PREDICTION_COL, ML_PREDICTION_COL, "noise"])

    def test_uses_the_meta_model_when_both_estimates_are_present(self):
        model = self._fitted_model()
        prediction, fallback_used = predict_with_fallback(
            model, {"noise": 0.5}, [MARKOV_PREDICTION_COL, ML_PREDICTION_COL, "noise"],
            markov_p=0.5, ml_p=0.9,
        )
        assert fallback_used is False
        assert 0.0 <= prediction <= 1.0

    def test_falls_back_to_markov_when_ml_is_missing(self):
        model = self._fitted_model()
        prediction, fallback_used = predict_with_fallback(
            model, {"noise": 0.5}, [MARKOV_PREDICTION_COL, ML_PREDICTION_COL, "noise"],
            markov_p=0.65, ml_p=None,
        )
        assert fallback_used is True
        assert prediction == 0.65

    def test_falls_back_to_ml_when_markov_is_missing(self):
        model = self._fitted_model()
        prediction, fallback_used = predict_with_fallback(
            model, {"noise": 0.5}, [MARKOV_PREDICTION_COL, ML_PREDICTION_COL, "noise"],
            markov_p=None, ml_p=0.72,
        )
        assert fallback_used is True
        assert prediction == 0.72

    def test_returns_none_when_both_are_missing(self):
        model = self._fitted_model()
        prediction, fallback_used = predict_with_fallback(
            model, {"noise": 0.5}, [MARKOV_PREDICTION_COL, ML_PREDICTION_COL, "noise"],
            markov_p=None, ml_p=None,
        )
        assert prediction is None
        assert fallback_used is True
