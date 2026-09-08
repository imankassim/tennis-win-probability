import random

import pytest

from evaluation.metrics import expected_calibration_error
from pricing.calibration.calibration import (
    IsotonicCalibrator,
    NoCalibration,
    PhaseCalibrator,
    PlattCalibrator,
    match_phase,
)


def _miscalibrated_dataset(n=2000, seed=0):
    """A dataset where the model is systematically overconfident: it
    predicts p, but the true outcome rate is only p/2. Any real
    calibrator should reduce ECE on this; NoCalibration should not."""
    rng = random.Random(seed)
    predictions = []
    actuals = []
    for _ in range(n):
        p = rng.uniform(0.05, 0.95)
        true_rate = p / 2
        predictions.append(p)
        actuals.append(1.0 if rng.random() < true_rate else 0.0)
    return predictions, actuals


class TestNoCalibration:
    def test_returns_predictions_unchanged(self):
        cal = NoCalibration().fit([0.3, 0.7], [0.0, 1.0])
        assert cal.predict([0.3, 0.7]) == [0.3, 0.7]


class TestPlattCalibrator:
    def test_reduces_calibration_error_on_a_miscalibrated_dataset(self):
        train_p, train_a = _miscalibrated_dataset(seed=1)
        test_p, test_a = _miscalibrated_dataset(seed=2)

        raw_ece = expected_calibration_error(test_p, test_a)
        calibrated = PlattCalibrator().fit(train_p, train_a).predict(test_p)
        calibrated_ece = expected_calibration_error(calibrated, test_a)

        assert calibrated_ece < raw_ece

    def test_output_stays_within_zero_one(self):
        train_p, train_a = _miscalibrated_dataset(seed=1)
        cal = PlattCalibrator().fit(train_p, train_a)
        out = cal.predict([0.0, 0.5, 1.0])
        assert all(0.0 <= v <= 1.0 for v in out)


class TestIsotonicCalibrator:
    def test_reduces_calibration_error_on_a_miscalibrated_dataset(self):
        train_p, train_a = _miscalibrated_dataset(seed=1)
        test_p, test_a = _miscalibrated_dataset(seed=2)

        raw_ece = expected_calibration_error(test_p, test_a)
        calibrated = IsotonicCalibrator().fit(train_p, train_a).predict(test_p)
        calibrated_ece = expected_calibration_error(calibrated, test_a)

        assert calibrated_ece < raw_ece

    def test_is_monotonic_in_the_input(self):
        train_p, train_a = _miscalibrated_dataset(seed=1)
        cal = IsotonicCalibrator().fit(train_p, train_a)
        low, mid, high = cal.predict([0.1, 0.5, 0.9])
        assert low <= mid <= high


class TestMatchPhase:
    @pytest.mark.parametrize(
        "set_no,best_of,expected",
        [
            (1, 3, "early"),
            (2, 3, "mid"),
            (3, 3, "deciding"),
            (1, 5, "early"),
            (2, 5, "early"),
            (3, 5, "mid"),
            (4, 5, "deciding"),
            (5, 5, "deciding"),
        ],
    )
    def test_classifies_set_number_into_a_phase(self, set_no, best_of, expected):
        assert match_phase(set_no, best_of) == expected


class TestPhaseCalibrator:
    def test_reduces_calibration_error_on_a_miscalibrated_dataset(self):
        train_p, train_a = _miscalibrated_dataset(n=3000, seed=1)
        test_p, test_a = _miscalibrated_dataset(n=1000, seed=2)
        rng = random.Random(3)
        train_phases = [rng.choice(["early", "mid", "deciding"]) for _ in train_p]
        test_phases = [rng.choice(["early", "mid", "deciding"]) for _ in test_p]

        raw_ece = expected_calibration_error(test_p, test_a)
        cal = PhaseCalibrator(min_samples_per_phase=100).fit(train_p, train_a, train_phases)
        calibrated = cal.predict(test_p, test_phases)
        calibrated_ece = expected_calibration_error(calibrated, test_a)

        assert calibrated_ece < raw_ece

    def test_falls_back_to_the_global_calibrator_for_a_sparse_phase(self):
        train_p, train_a = _miscalibrated_dataset(n=500, seed=1)
        train_phases = ["early"] * len(train_p)  # "deciding" never seen in training

        cal = PhaseCalibrator(min_samples_per_phase=100).fit(train_p, train_a, train_phases)
        # Must not raise, and must still return a valid probability.
        result = cal.predict([0.6], ["deciding"])
        assert 0.0 <= result[0] <= 1.0

    def test_rejects_mismatched_lengths(self):
        with pytest.raises(ValueError):
            PhaseCalibrator().fit([0.5, 0.5], [1.0, 0.0], ["early"])
