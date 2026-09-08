"""The recursive point-to-match Markov formulas (Klaassen & Magnus, 2003 —
see docs/REFERENCES.md). Pure math: given each player's probability of
winning a point on their own serve, compute the probability of winning a
game, a tiebreak, a set, or the match, from any current score state.

Every function takes the state "entering" the next point (points/games/sets
already completed), matching how state is stored elsewhere in this
codebase (database/models.py's Point, match_state.py's game_score_before).

No data, no I/O — serve-rate estimation (serve_rate.py) is a separate
concern, deliberately kept apart so this module can be tested purely on
its mathematical properties (symmetry, monotonicity, known closed forms).
"""

from __future__ import annotations

from functools import lru_cache

# Bounded, not unlimited: each unique (p_a, p_b) serve-rate pair produces
# its own family of cache entries that are essentially single-use once a
# match's evaluation moves on to a different pair — reused heavily within
# one match's points, never again after. Measured directly: with an
# unbounded cache, evaluating 2,000 real matches took 93s (vs 1s for 200
# matches) — not because the math got slower, but because Python's
# garbage collector re-scans an ever-growing cache on every cycle. A
# bounded cache evicts old, no-longer-useful entries and keeps this
# roughly linear in the number of points evaluated, whether serving one
# live match or bulk-evaluating thousands (evaluation/evaluate_markov.py).
_CACHE_SIZE = 100_000


@lru_cache(maxsize=_CACHE_SIZE)
def prob_win_game(p: float, a: int = 0, b: int = 0) -> float:
    """Probability the server wins their own service game, given `p` =
    their probability of winning any single point on serve, from a score
    of `a`-`b` (server-receiver) points already played in this game."""
    if a >= 4 and a - b >= 2:
        return 1.0
    if b >= 4 and b - a >= 2:
        return 0.0
    if a >= 3 and b >= 3:
        # Beyond deuce, only the difference matters — collapse to one of
        # three equivalent states so recursion terminates in O(1) steps
        # instead of following every possible deuce/advantage sequence.
        diff = a - b
        if diff == 0:
            # From deuce: win outright next point, or return to deuce.
            return (p * p) / (p * p + (1 - p) * (1 - p))
        if diff == 1:
            # Advantage server: win outright, or fall back to deuce.
            deuce = prob_win_game(p, 3, 3)
            return p + (1 - p) * deuce
        # diff == -1: advantage receiver — survive only by winning the
        # point back to deuce, then must win from deuce.
        deuce = prob_win_game(p, 3, 3)
        return p * deuce
    return p * prob_win_game(p, a + 1, b) + (1 - p) * prob_win_game(p, a, b + 1)


def _tiebreak_server_is_a(point_number: int, a_serves_point_1: bool) -> bool:
    """Who serves tiebreak point `point_number` (1-indexed): server changes
    after point 1, then every 2 points — the standard rotation
    (1 | 2,3 | 4,5 | 6,7 | ...)."""
    if point_number == 1:
        return a_serves_point_1
    pair = (point_number - 2) // 2
    other_player_serves_this_pair = pair % 2 == 0
    return (not a_serves_point_1) if other_player_serves_this_pair else a_serves_point_1


# Unlike a service game, a tiebreak has no constant-probability "deuce"
# state to collapse to a closed form (the server, and so the point-win
# probability, alternates every 2 points even deep into extra points). The
# true recursion is an infinite series for evenly matched players. Capped
# here instead: past this many combined points, the remaining outcome is
# treated as a coin flip. Reaching this deep (well past 20-20) has
# vanishingly small probability in any realistic scenario, so the
# truncation error is negligible — and it keeps this a plain, auditable
# recursion rather than an iterative approximation.
_TIEBREAK_TRUNCATION_POINTS = 40


@lru_cache(maxsize=_CACHE_SIZE)
def prob_win_tiebreak(
    p_a: float, p_b: float, a: int = 0, b: int = 0, a_serves_point_1: bool = True
) -> float:
    """Probability player A wins a 7-point tiebreak (win by 2), from a
    score of `a`-`b` points, given who serves the breaker's first point."""
    if a >= 7 and a - b >= 2:
        return 1.0
    if b >= 7 and b - a >= 2:
        return 0.0
    if a + b >= _TIEBREAK_TRUNCATION_POINTS:
        return 0.5

    a_serves_next_point = _tiebreak_server_is_a(a + b + 1, a_serves_point_1)
    p_a_wins_point = p_a if a_serves_next_point else 1 - p_b

    return p_a_wins_point * prob_win_tiebreak(p_a, p_b, a + 1, b, a_serves_point_1) + (
        1 - p_a_wins_point
    ) * prob_win_tiebreak(p_a, p_b, a, b + 1, a_serves_point_1)


@lru_cache(maxsize=_CACHE_SIZE)
def prob_win_set(
    p_a: float,
    p_b: float,
    games_a: int = 0,
    games_b: int = 0,
    a_serves_next: bool = True,
    points_a: int = 0,
    points_b: int = 0,
) -> float:
    """Probability player A wins the set from `games_a`-`games_b` games
    (plus an optional in-progress current game at `points_a`-`points_b`),
    given who serves the game currently being played."""
    if games_a >= 6 and games_a - games_b >= 2:
        return 1.0
    if games_b >= 6 and games_b - games_a >= 2:
        return 0.0
    if games_a == 6 and games_b == 6:
        return prob_win_tiebreak(p_a, p_b, a_serves_point_1=a_serves_next)

    p_server = p_a if a_serves_next else p_b
    p_a_wins_this_game = (
        prob_win_game(p_server, points_a, points_b)
        if a_serves_next
        else 1 - prob_win_game(p_server, points_b, points_a)
    )
    return p_a_wins_this_game * prob_win_set(
        p_a, p_b, games_a + 1, games_b, not a_serves_next
    ) + (1 - p_a_wins_this_game) * prob_win_set(
        p_a, p_b, games_a, games_b + 1, not a_serves_next
    )


@lru_cache(maxsize=_CACHE_SIZE)
def prob_win_match(
    p_a: float,
    p_b: float,
    best_of: int = 3,
    sets_a: int = 0,
    sets_b: int = 0,
    games_a: int = 0,
    games_b: int = 0,
    a_serves_next: bool = True,
    points_a: int = 0,
    points_b: int = 0,
) -> float:
    """Probability player A wins the match from the given state."""
    sets_needed = best_of // 2 + 1
    if sets_a >= sets_needed:
        return 1.0
    if sets_b >= sets_needed:
        return 0.0

    p_a_wins_this_set = prob_win_set(
        p_a, p_b, games_a, games_b, a_serves_next, points_a, points_b
    )
    # The next set (if any) always starts 0-0 games, served by whoever is
    # next in the alternation — approximated here as continuing from the
    # server due up, which is exact when the just-finished set had an even
    # number of games (always true except after a tiebreak set, a known,
    # documented simplification).
    return p_a_wins_this_set * prob_win_match(
        p_a, p_b, best_of, sets_a + 1, sets_b, 0, 0, a_serves_next
    ) + (1 - p_a_wins_this_set) * prob_win_match(
        p_a, p_b, best_of, sets_a, sets_b + 1, 0, 0, a_serves_next
    )
