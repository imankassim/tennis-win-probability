"""Calibration methods (Journey 13): EXP40-43. Maps a raw (blended)
probability onto empirically observed outcome frequencies — the last
learned step before trading_rules/ applies margin and bounds.

All calibrators share the same tiny interface (fit, predict) so
evaluation code doesn't need to know which one it's holding — including
NoCalibration (EXP40), the "do nothing" baseline every other method is
compared against, the same role EXP1 plays for the whole project.
"""

from __future__ import annotations

from collections import defaultdict

from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression


class NoCalibration:
    """EXP40: the raw probability, unchanged. The baseline the other
    three methods are compared against."""

    def fit(self, predictions: list[float], actuals: list[float]) -> "NoCalibration":
        return self

    def predict(self, predictions: list[float]) -> list[float]:
        return list(predictions)


class PlattCalibrator:
    """EXP41: fits a logistic regression on the raw probability as its
    single feature — the classic Platt scaling recipe."""

    def __init__(self) -> None:
        self._model = LogisticRegression()

    def fit(self, predictions: list[float], actuals: list[float]) -> "PlattCalibrator":
        x = [[p] for p in predictions]
        self._model.fit(x, actuals)
        return self

    def predict(self, predictions: list[float]) -> list[float]:
        x = [[p] for p in predictions]
        return self._model.predict_proba(x)[:, 1].tolist()


class IsotonicCalibrator:
    """EXP42: a monotonic, non-parametric mapping — more flexible than
    Platt's fixed logistic shape, at the cost of needing more data to fit
    reliably."""

    def __init__(self) -> None:
        self._model = IsotonicRegression(out_of_bounds="clip")

    def fit(self, predictions: list[float], actuals: list[float]) -> "IsotonicCalibrator":
        self._model.fit(predictions, actuals)
        return self

    def predict(self, predictions: list[float]) -> list[float]:
        return self._model.predict(predictions).tolist()


def match_phase(set_no: int, best_of: int) -> str:
    """A simple three-way split — early / mid / deciding — coarse enough
    that each phase still gets enough data to calibrate against."""
    if best_of == 5:
        if set_no <= 2:
            return "early"
        if set_no == 3:
            return "mid"
        return "deciding"
    # best_of == 3
    if set_no == 1:
        return "early"
    if set_no == 2:
        return "mid"
    return "deciding"


class PhaseCalibrator:
    """EXP43: a separate IsotonicCalibrator per match phase
    (match_phase), falling back to one global calibrator for any phase
    that doesn't have enough data to fit its own reliably — matching the
    charter's "error broken down by match phase" evaluation measure with
    an actual calibration response to it, not just a reporting split."""

    def __init__(self, min_samples_per_phase: int = 500) -> None:
        self._min_samples = min_samples_per_phase
        self._phase_models: dict[str, IsotonicCalibrator] = {}
        self._fallback = IsotonicCalibrator()

    def fit(
        self, predictions: list[float], actuals: list[float], phases: list[str]
    ) -> "PhaseCalibrator":
        if len(predictions) != len(phases):
            raise ValueError("predictions and phases must be the same length")
        self._fallback.fit(predictions, actuals)

        by_phase: dict[str, tuple[list[float], list[float]]] = defaultdict(lambda: ([], []))
        for p, a, phase in zip(predictions, actuals, phases):
            by_phase[phase][0].append(p)
            by_phase[phase][1].append(a)

        for phase, (preds, acts) in by_phase.items():
            if len(preds) >= self._min_samples:
                self._phase_models[phase] = IsotonicCalibrator().fit(preds, acts)

        return self

    def predict(self, predictions: list[float], phases: list[str]) -> list[float]:
        if len(predictions) != len(phases):
            raise ValueError("predictions and phases must be the same length")
        out = []
        for p, phase in zip(predictions, phases):
            model = self._phase_models.get(phase, self._fallback)
            out.append(model.predict([p])[0])
        return out
