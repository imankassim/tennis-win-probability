"""Combines the Markov and ML estimates (Journey 12): EXP30-33.

Deliberately the simplest possible combination - a weighted average - not
a learned meta-model (that's EXP34/Journey 14). The weight-tuning search
(`tune_weight`) is a separate function from the combination formula
itself so the formula stays trivially testable on its own.
"""

from __future__ import annotations

from evaluation.metrics import brier_score


def blend_probability(markov_p: float, ml_p: float, markov_weight: float) -> float:
    """A weighted average of the two independent estimates.
    markov_weight=1.0 reduces to Markov-only (EXP30); 0.0 to ML-only
    (EXP31)."""
    if not 0.0 <= markov_weight <= 1.0:
        raise ValueError("markov_weight must be between 0 and 1")
    return markov_weight * markov_p + (1 - markov_weight) * ml_p


def tune_weight(
    markov_predictions: list[float],
    ml_predictions: list[float],
    actuals: list[float],
    step: float = 0.05,
) -> tuple[float, float]:
    """EXP33: sweeps markov_weight from 0.0 to 1.0 on a validation set
    (never the final test set - that would leak the tuning decision into
    the reported result) and returns (best_weight, its_brier_score)."""
    if len(markov_predictions) != len(ml_predictions) or len(markov_predictions) != len(
        actuals
    ):
        raise ValueError("markov_predictions, ml_predictions and actuals must be the same length")

    best_weight = 0.0
    best_brier = float("inf")
    weight = 0.0
    while weight <= 1.0 + 1e-9:
        w = min(weight, 1.0)
        blended = [blend_probability(m, ml, w) for m, ml in zip(markov_predictions, ml_predictions)]
        score = brier_score(blended, actuals)
        if score < best_brier:
            best_brier = score
            best_weight = w
        weight += step

    return best_weight, best_brier
