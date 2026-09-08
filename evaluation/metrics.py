"""Evaluation metrics (Journey 8): Brier score, log-loss, latency
percentiles. Pure functions over plain lists — no dependency on any
particular estimator, repository or database, so the same code evaluates
EXP1, EXP2, and later the Markov/ML/blend configurations, per the
"same evaluation framework across stages" principle.
"""

from __future__ import annotations

import math

_LOG_LOSS_EPSILON = 1e-15


def brier_score(predictions: list[float], outcomes: list[float]) -> float:
    """Mean squared error between predicted probability (of the outcome
    being 1) and the actual outcome (0 or 1). Lower is better; 0 is
    perfect, 0.25 is what always-guessing-0.5 scores against a balanced
    field."""
    if len(predictions) != len(outcomes):
        raise ValueError("predictions and outcomes must be the same length")
    if not predictions:
        raise ValueError("cannot score an empty set of predictions")
    return sum((p - o) ** 2 for p, o in zip(predictions, outcomes)) / len(predictions)


def log_loss(predictions: list[float], outcomes: list[float]) -> float:
    """Binary cross-entropy. Lower is better; penalises confident wrong
    predictions much more heavily than Brier score does. Predictions are
    clipped away from exactly 0/1 so a single confident miss can't produce
    an infinite score."""
    if len(predictions) != len(outcomes):
        raise ValueError("predictions and outcomes must be the same length")
    if not predictions:
        raise ValueError("cannot score an empty set of predictions")
    total = 0.0
    for p, o in zip(predictions, outcomes):
        p_clipped = min(max(p, _LOG_LOSS_EPSILON), 1 - _LOG_LOSS_EPSILON)
        total += -(o * math.log(p_clipped) + (1 - o) * math.log(1 - p_clipped))
    return total / len(predictions)


def percentile(values: list[float], pct: float) -> float:
    """Nearest-rank percentile (0-100). No interpolation — simple and
    sufficient for reporting p50/p95 latency; not a statistical estimator."""
    if not values:
        raise ValueError("cannot take a percentile of an empty list")
    if not 0 <= pct <= 100:
        raise ValueError("pct must be between 0 and 100")
    ordered = sorted(values)
    index = max(0, math.ceil(pct / 100 * len(ordered)) - 1)
    return ordered[index]
