"""Serve-rate estimation (EXP10, EXP11, EXP13) from our own ingested match
archive — the input to the Markov formulas (formulas.py).

Every function takes `as_of_date` and strictly excludes points from
matches on or after it, the same no-look-ahead discipline as
backend/context_features.py.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date

from database.models import Match, Point

# EXP13: pseudo-count strength for Bayesian shrinkage toward the tour
# average — the sparse-data risk in docs/architecture/risk_register.md.
# Chosen as roughly "20 service points' worth" of trust in the tour prior;
# not tuned against held-out data yet (that tuning is a follow-up
# experiment, not this journey's job).
DEFAULT_SHRINKAGE_STRENGTH = 20

# Used only when there is no tour history at all before as_of_date (the
# very first matches in the archive) — a reasonable tour-level serve rate,
# not fitted to any data. Graceful degradation, not a silent zero. Single
# source of truth for pricing/markov/engine.py too.
COLD_START_SERVE_RATE = 0.6


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


def bulk_shrunk_serve_rates(
    matches: list[Match],
    points_by_match: dict[str, list[Point]],
    shrinkage_strength: int = DEFAULT_SHRINKAGE_STRENGTH,
) -> dict[str, tuple[float, float]]:
    """The same (p_a, p_b) `serve_rate_with_shrinkage` would give for every
    match, but computed in one pass through the archive in date order,
    maintaining running per-player and tour-wide counts — O(total points)
    instead of O(matches x archive size).

    Calling `serve_rate_with_shrinkage` once per match (the natural way to
    write it) re-scans the entire prior archive for every single match,
    which is fine for one live request but becomes quadratic when
    bulk-evaluating thousands of matches (evaluation/evaluate_markov.py).
    This mirrors the same running-totals approach as
    backend/player_rating.py's compute_rating_history — same no-look-ahead
    guarantee (a match's own points update the running counts only after
    its rate has been computed), same result, far less work.
    """
    player_served: dict[str, int] = defaultdict(int)
    player_won: dict[str, int] = defaultdict(int)
    tour_served = 0
    tour_won = 0

    resolvable = [m for m in matches if points_by_match.get(m.match_id)]
    result: dict[str, tuple[float, float]] = {}

    for match in sorted(resolvable, key=lambda m: m.match_date):
        tour_avg = (tour_won / tour_served) if tour_served > 0 else COLD_START_SERVE_RATE

        def _shrunk(player_id: str) -> float:
            served = player_served[player_id]
            won = player_won[player_id]
            return (won + shrinkage_strength * tour_avg) / (served + shrinkage_strength)

        result[match.match_id] = (_shrunk(match.player_a_id), _shrunk(match.player_b_id))

        for point in points_by_match[match.match_id]:
            server_id = match.player_a_id if point.server == "player_a" else match.player_b_id
            player_served[server_id] += 1
            tour_served += 1
            if point.point_winner == point.server:
                player_won[server_id] += 1
                tour_won += 1

    return result
