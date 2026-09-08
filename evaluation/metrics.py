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


def reliability_bins(
    predictions: list[float], outcomes: list[float], n_bins: int = 10
) -> list[dict]:
    """Buckets predictions into `n_bins` equal-width bins on [0, 1] and
    returns, per non-empty bin: the mean predicted probability, the
    observed outcome rate, and the bin's point count. A perfectly
    calibrated model has mean_predicted == observed_rate in every bin —
    this is the data a reliability diagram plots, and what
    expected_calibration_error summarises into one number."""
    if len(predictions) != len(outcomes):
        raise ValueError("predictions and outcomes must be the same length")
    if not predictions:
        raise ValueError("cannot bin an empty set of predictions")

    buckets: list[list[tuple[float, float]]] = [[] for _ in range(n_bins)]
    for p, o in zip(predictions, outcomes):
        index = min(int(p * n_bins), n_bins - 1)
        buckets[index].append((p, o))

    bins = []
    for bucket in buckets:
        if not bucket:
            continue
        preds = [p for p, _ in bucket]
        obs = [o for _, o in bucket]
        bins.append(
            {
                "mean_predicted": sum(preds) / len(preds),
                "observed_rate": sum(obs) / len(obs),
                "count": len(bucket),
            }
        )
    return bins


def expected_calibration_error(
    predictions: list[float], outcomes: list[float], n_bins: int = 10
) -> float:
    """ECE: the count-weighted average gap between predicted probability
    and observed outcome rate, across `n_bins` equal-width bins. 0 is
    perfectly calibrated; there's no fixed "good" threshold the way
    Brier/log-loss have natural comparators — it's read relative to other
    configurations evaluated the same way."""
    bins = reliability_bins(predictions, outcomes, n_bins)
    total = sum(b["count"] for b in bins)
    return sum(
        b["count"] * abs(b["mean_predicted"] - b["observed_rate"]) for b in bins
    ) / total
