"""Failure-injection tests (Journey 18): the non-functional requirement
this project's source document states explicitly - "a failure in the ML,
blend or calibration layer must not prevent the Markov baseline from
serving where it remains available" - exercised directly rather than
just asserted in a docstring.
"""

from datetime import date

import numpy as np
import pytest

from backend.probability import MARKOV_MODEL_VERSION, compute_probability, load_artefacts
from database.models import Match, Point
from pricing.promote_model import PricingArtefacts

A, B = "player_a_id", "player_b_id"


def _match():
    return Match(
        match_id="m1",
        tournament="t",
        round="F",
        surface="hard",
        best_of=3,
        match_date=date(2026, 1, 1),
        player_a_id=A,
        player_b_id=B,
        source="test",
    )


class _RaisingModel:
    def predict_proba(self, x):
        raise RuntimeError("simulated ML model failure")


class _WorkingModel:
    def predict_proba(self, x):
        return np.array([[0.4, 0.6]])


class _RaisingCalibrator:
    def predict(self, predictions, phases):
        raise RuntimeError("simulated calibrator failure")


class _WorkingCalibrator:
    def predict(self, predictions, phases):
        return [p - 0.1 for p in predictions]


def _artefacts(ml_model, calibrator) -> PricingArtefacts:
    return PricingArtefacts(
        version="20260101T000000Z",
        model_version="blend_v1_calibrated",
        ml_model=ml_model,
        calibrator=calibrator,
        blend_markov_weight=0.15,
        feature_columns=[
            "best_of", "sets_a", "sets_b", "games_a", "games_b", "server_is_a",
            "form_a", "form_b", "surface_rate_a", "surface_rate_b", "h2h_rate_a",
            "elo_a", "elo_b", "momentum_a",
        ],
        trained_at="2026-01-01T00:00:00+00:00",
        n_training_matches=10,
        n_calibration_matches=2,
        calibration_brier=0.2,
        calibration_log_loss=0.5,
        calibration_ece=0.05,
    )


def _compute(artefacts):
    return compute_probability(
        artefacts=artefacts,
        match=_match(),
        points_so_far=[],
        context={},
        p_a_serve_rate=0.6,
        p_b_serve_rate=0.6,
        sets_won_a=0,
        sets_won_b=0,
        games_won_a=0,
        games_won_b=0,
        server="player_a",
    )


def test_no_artefacts_degrades_to_markov_only():
    result = _compute(artefacts=None)
    assert result.model_version == MARKOV_MODEL_VERSION
    assert result.fallback_used is True
    assert result.widen_margin is False
    assert 0.0 <= result.probability_a <= 1.0
    # No ML estimate was ever attempted, but the Markov one is still
    # exposed - here it's identical to the served probability, since
    # there was nothing to blend it with.
    assert result.markov_probability_a == result.probability_a
    assert result.ml_probability_a is None


def test_working_pipeline_uses_the_promoted_model_version():
    result = _compute(_artefacts(_WorkingModel(), _WorkingCalibrator()))
    assert result.model_version == "blend_v1_calibrated"
    assert result.fallback_used is False
    assert result.widen_margin is False
    # Both raw estimates are exposed alongside the final served value -
    # the whole point of markov_probability_a/ml_probability_a existing
    # (docs/ethics/assessment.md's explainability gap).
    assert 0.0 <= result.markov_probability_a <= 1.0
    assert result.ml_probability_a == pytest.approx(0.6)  # _WorkingModel's fixed prediction
    # The final served value went through blend + calibration, so it
    # shouldn't just equal either raw input.
    assert result.probability_a != result.markov_probability_a
    assert result.probability_a != result.ml_probability_a


def test_ml_model_failure_falls_back_to_markov_without_widening_margin():
    """The ML model raising (a bad feature row, a version-incompatible
    pickle, anything) must not prevent Markov from serving - the
    reliability requirement this journey exists to verify. Matches
    docs/architecture/deployment.md's "ML model unavailable" row: plain
    Markov-only, not the widened-margin treatment (that row is reserved
    for when blend/calibration discards an ML estimate that already
    succeeded - see the next test)."""
    markov_only = _compute(artefacts=None)
    with pytest.warns(UserWarning, match="ML model failed"):
        result = _compute(_artefacts(_RaisingModel(), _WorkingCalibrator()))
    assert result.model_version == MARKOV_MODEL_VERSION
    assert result.fallback_used is True
    assert result.widen_margin is False
    assert result.probability_a == markov_only.probability_a
    # The ML model never produced a value at all here.
    assert result.markov_probability_a == result.probability_a
    assert result.ml_probability_a is None


def test_calibrator_failure_falls_back_to_markov_with_a_widened_margin():
    """Matches docs/architecture/deployment.md's "blend or calibration
    unavailable" row exactly: Markov-only, but with widen_margin=True so
    the caller prices more cautiously - a successfully-computed ML
    estimate was discarded here, unlike the plain ML-failure case."""
    markov_only = _compute(artefacts=None)
    with pytest.warns(UserWarning, match="Blend/calibration failed"):
        result = _compute(_artefacts(_WorkingModel(), _RaisingCalibrator()))
    assert result.model_version == MARKOV_MODEL_VERSION
    assert result.fallback_used is True
    assert result.widen_margin is True
    assert result.probability_a == markov_only.probability_a
    # Unlike the ML-failure case, the ML model DID succeed here before
    # blend/calibration failed - that real prediction is still exposed,
    # even though it wasn't used in the (Markov-only) served value.
    assert result.markov_probability_a == result.probability_a
    assert result.ml_probability_a == pytest.approx(0.6)


def test_load_artefacts_returns_none_when_no_file_exists(tmp_path):
    assert load_artefacts(directory=tmp_path) is None


def test_load_artefacts_degrades_on_a_corrupted_file_instead_of_raising(tmp_path):
    (tmp_path / "pricing_pipeline.joblib").write_bytes(b"not a real pickle")
    with pytest.warns(UserWarning, match="Failed to load pricing artefacts"):
        result = load_artefacts(directory=tmp_path)
    assert result is None
