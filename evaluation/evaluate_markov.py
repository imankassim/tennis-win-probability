"""Evaluates the Markov engine (pricing/markov/) against real match data.

Separate from harness.py rather than reusing its generic ProbabilityFn:
the Markov engine needs per-match context (best_of, who's serving, and
serve rates specific to that match's two players) that a
(sets_a, sets_b, games_a, games_b) -> probability signature can't express.
It still reuses evaluation/metrics.py, so results are directly comparable
to EXP1/EXP2's harness.py-based numbers.
"""

from __future__ import annotations

from database.models import Match, OutcomeLabel, Point
from evaluation.harness import EvaluationResult
from evaluation.metrics import brier_score, log_loss
from pricing.markov.engine import estimate_match_serve_rates, markov_probability


def evaluate_markov(
    configuration_name: str,
    matches: list[Match],
    points_by_match: dict[str, list[Point]],
    outcomes: dict[str, OutcomeLabel],
) -> EvaluationResult:
    predictions: list[float] = []
    actuals: list[float] = []
    n_matches = 0

    for match in matches:
        outcome = outcomes.get(match.match_id)
        points = points_by_match.get(match.match_id)
        if outcome is None or not points:
            continue
        n_matches += 1
        p_a, p_b = estimate_match_serve_rates(match, matches, points_by_match)
        actual = 1.0 if outcome.actual_winner == "player_a" else 0.0
        for point in points:
            prediction = markov_probability(
                p_a,
                p_b,
                match.best_of,
                point.sets_won_a,
                point.sets_won_b,
                point.games_won_a,
                point.games_won_b,
                point.server,
            )
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
