"""Ties the recursive formulas (formulas.py) to serve-rate estimation
(serve_rate.py) into a single "Markov chain" probability engine — the
EXP10/EXP11/EXP13 analytic baseline, journey 9's main deliverable.
"""

from __future__ import annotations

from datetime import date

from database.models import Match, Point
from pricing.markov.formulas import prob_win_match
from pricing.markov.serve_rate import (
    COLD_START_SERVE_RATE,
    serve_rate_with_shrinkage,
    tour_average_serve_rate,
)

__all__ = ["COLD_START_SERVE_RATE", "estimate_match_serve_rates", "markov_probability"]


def estimate_match_serve_rates(
    match: Match,
    matches: list[Match],
    points_by_match: dict[str, list[Point]],
) -> tuple[float, float]:
    """(player_a serve rate, player_b serve rate), each shrunk toward the
    tour average (EXP13), as of this match's own date — no look-ahead."""
    try:
        tour_average_serve_rate(matches, points_by_match, match.match_date)
    except ValueError:
        return COLD_START_SERVE_RATE, COLD_START_SERVE_RATE

    p_a = serve_rate_with_shrinkage(
        match.player_a_id, matches, points_by_match, match.match_date
    )
    p_b = serve_rate_with_shrinkage(
        match.player_b_id, matches, points_by_match, match.match_date
    )
    return p_a, p_b


def markov_probability(
    p_a: float,
    p_b: float,
    best_of: int,
    sets_a: int,
    sets_b: int,
    games_a: int,
    games_b: int,
    server: str,
    points_a: int = 0,
    points_b: int = 0,
) -> float:
    """Probability player A wins the match from the current state, given
    each player's (shrunk) serve-win probability."""
    return prob_win_match(
        p_a,
        p_b,
        best_of,
        sets_a,
        sets_b,
        games_a,
        games_b,
        a_serves_next=(server == "player_a"),
        points_a=points_a,
        points_b=points_b,
    )
