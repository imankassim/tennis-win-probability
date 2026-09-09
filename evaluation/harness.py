"""The evaluation harness (Journey 8): scores a probability function
against confirmed match outcomes, using the same metrics module for any
configuration - EXP1, EXP2, and later the Markov/ML/blend estimators.

Not a train/test split yet: EXP1 and EXP2 are fixed, untuned heuristics
with nothing to overfit, so evaluating on the full available dataset is
fine. Match-level splitting (docs/architecture/offline-training-architecture.md's
training controls) starts to matter once a configuration is actually
fitted to data - from Journey 9's Markov parameter tuning onward.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from database.models import Match, OutcomeLabel, Point
from evaluation.metrics import brier_score, log_loss

ProbabilityFn = Callable[[int, int, int, int], float]
"""(sets_won_a, sets_won_b, games_won_a, games_won_b) -> probability player_a wins."""


@dataclass(frozen=True)
class EvaluationResult:
    configuration: str
    n_points: int
    n_matches: int
    brier: float
    log_loss: float


def evaluate_configuration(
    configuration_name: str,
    probability_fn: ProbabilityFn,
    matches: list[Match],
    points_by_match: dict[str, list[Point]],
    outcomes: dict[str, OutcomeLabel],
) -> EvaluationResult:
    """Scores `probability_fn` at every point of every match that has a
    confirmed outcome. Matches without one (quarantined as incomplete) are
    excluded, not guessed at - consistent with the quarantine-on-failure
    rule."""
    matches_by_id = {m.match_id: m for m in matches}
    predictions: list[float] = []
    actuals: list[float] = []
    n_matches = 0

    for match_id, points in points_by_match.items():
        outcome = outcomes.get(match_id)
        if outcome is None or match_id not in matches_by_id:
            continue
        n_matches += 1
        actual = 1.0 if outcome.actual_winner == "player_a" else 0.0
        for p in points:
            prediction = probability_fn(p.sets_won_a, p.sets_won_b, p.games_won_a, p.games_won_b)
            predictions.append(prediction)
            actuals.append(actual)

    if not predictions:
        raise ValueError("no points from matches with a confirmed outcome to evaluate")

    return EvaluationResult(
        configuration=configuration_name,
        n_points=len(predictions),
        n_matches=n_matches,
        brier=brier_score(predictions, actuals),
        log_loss=log_loss(predictions, actuals),
    )
