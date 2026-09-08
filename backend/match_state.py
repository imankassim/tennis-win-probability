"""The match-state parser (logical architecture component B1): normalises
a raw point event and tracks whether it's a break point.

Deferred from ingestion (Journey 4) and the first API pass (Journey 5)
because it needs within-game point-by-point reconstruction, which those
stages deliberately avoided (see database/ingestion/outcomes.py's
docstring for why). It's derivable from already-stored data with no new
fields: for any point, look at the earlier points in the same game_no and
tally who won them.
"""

from __future__ import annotations

from database.models import Point


def _other(side: str) -> str:
    return "player_b" if side == "player_a" else "player_a"


def game_score_before(points: list[Point], target: Point) -> tuple[int, int]:
    """Points won by (player_a, player_b) within target's game, strictly
    before target itself."""
    prior = [
        p for p in points if p.game_no == target.game_no and p.point_no < target.point_no
    ]
    won_a = sum(1 for p in prior if p.point_winner == "player_a")
    won_b = sum(1 for p in prior if p.point_winner == "player_b")
    return won_a, won_b


def is_break_point(receiver_points: int, server_points: int) -> bool:
    """True when the receiver is one point from winning the game: the same
    condition frontend/src/lib/scoring.ts uses for the mock dashboard,
    applied here to real data."""
    return receiver_points >= 3 and receiver_points - server_points >= 1


def compute_break_point(points: list[Point], target: Point) -> bool:
    won_a, won_b = game_score_before(points, target)
    receiver = _other(target.server)
    receiver_points = won_a if receiver == "player_a" else won_b
    server_points = won_b if receiver == "player_a" else won_a
    return is_break_point(receiver_points, server_points)
