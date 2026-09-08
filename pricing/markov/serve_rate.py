"""Serve-rate estimation (EXP10, EXP11, EXP13) from our own ingested match
archive — the input to the Markov formulas (formulas.py).

Every function takes `as_of_date` and strictly excludes points from
matches on or after it, the same no-look-ahead discipline as
backend/context_features.py.
"""

from __future__ import annotations

from datetime import date

from database.models import Match, Point

# EXP13: pseudo-count strength for Bayesian shrinkage toward the tour
# average — the sparse-data risk in docs/architecture/risk_register.md.
# Chosen as roughly "20 service points' worth" of trust in the tour prior;
# not tuned against held-out data yet (that tuning is a follow-up
# experiment, not this journey's job).
DEFAULT_SHRINKAGE_STRENGTH = 20


def _player_role(player_id: str, match: Match) -> str | None:
    if player_id == match.player_a_id:
        return "player_a"
    if player_id == match.player_b_id:
        return "player_b"
    return None


def _service_points_before(
    player_id: str,
    matches: list[Match],
    points_by_match: dict[str, list[Point]],
    as_of_date: date,
) -> tuple[int, int]:
    """(points served, points won on serve) for `player_id` across all
    matches strictly before as_of_date."""
    served = won = 0
    for match in matches:
        if match.match_date >= as_of_date:
            continue
        role = _player_role(player_id, match)
        if role is None:
            continue
        for point in points_by_match.get(match.match_id, []):
            if point.server != role:
                continue
            served += 1
            if point.point_winner == role:
                won += 1
    return served, won


def tour_average_serve_rate(
    matches: list[Match],
    points_by_match: dict[str, list[Point]],
    as_of_date: date,
) -> float:
    """EXP10: a single constant serve-win rate across every point played
    before as_of_date, regardless of player. The weakest Markov
    parameterisation — every later refinement is compared against it."""
    served = won = 0
    for match in matches:
        if match.match_date >= as_of_date:
            continue
        for point in points_by_match.get(match.match_id, []):
            served += 1
            if point.point_winner == point.server:
                won += 1
    if served == 0:
        raise ValueError("no points before as_of_date to estimate a tour average from")
    return won / served


def player_serve_rate(
    player_id: str,
    matches: list[Match],
    points_by_match: dict[str, list[Point]],
    as_of_date: date,
) -> float | None:
    """EXP11: a player's own empirical serve-win rate before as_of_date.
    None if they have no prior service points (an unknown quantity, not a
    default — callers should fall back to the tour average themselves, or
    use serve_rate_with_shrinkage)."""
    served, won = _service_points_before(player_id, matches, points_by_match, as_of_date)
    if served == 0:
        return None
    return won / served


def serve_rate_with_shrinkage(
    player_id: str,
    matches: list[Match],
    points_by_match: dict[str, list[Point]],
    as_of_date: date,
    shrinkage_strength: int = DEFAULT_SHRINKAGE_STRENGTH,
) -> float:
    """EXP13: Bayesian shrinkage toward the tour average, weighted by how
    much serve data the player actually has. A player with few recorded
    service points ends up close to the tour average; a well-covered
    player ends up close to their own empirical rate. Never fails — a
    player with zero data returns exactly the tour average.

    (player_won + k * tour_avg) / (player_served + k), a standard
    pseudo-count shrinkage estimator (k = shrinkage_strength).
    """
    tour_avg = tour_average_serve_rate(matches, points_by_match, as_of_date)
    served, won = _service_points_before(player_id, matches, points_by_match, as_of_date)
    return (won + shrinkage_strength * tour_avg) / (served + shrinkage_strength)
