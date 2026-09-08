from datetime import date

import pytest

from database.models import Match, Point
from pricing.markov.serve_rate import (
    DEFAULT_SHRINKAGE_STRENGTH,
    player_serve_rate,
    serve_rate_with_shrinkage,
    tour_average_serve_rate,
)

A, B, C = "player_a_id", "player_b_id", "player_c_id"


def _match(match_id, d, p1, p2):
    return Match(
        match_id=match_id,
        tournament="t",
        round="F",
        surface="hard",
        best_of=3,
        match_date=d,
        player_a_id=p1,
        player_b_id=p2,
        source="test",
    )


def _point(match_id, point_no, server, winner):
    return Point(
        match_id=match_id,
        point_no=point_no,
        set_no=1,
        game_no=1,
        server=server,
        point_winner=winner,
        sets_won_a=0,
        sets_won_b=0,
        games_won_a=0,
        games_won_b=0,
        point_score="n/a",
    )


def test_tour_average_across_all_players():
    matches = [_match("m1", date(2026, 1, 1), A, B)]
    # 4 points served by A (3 won), 4 served by B (1 won) -> 4/8 = 0.5
    points = {
        "m1": [
            _point("m1", 1, "player_a", "player_a"),
            _point("m1", 2, "player_a", "player_a"),
            _point("m1", 3, "player_a", "player_a"),
            _point("m1", 4, "player_a", "player_b"),
            _point("m1", 5, "player_b", "player_b"),
            _point("m1", 6, "player_b", "player_a"),
            _point("m1", 7, "player_b", "player_a"),
            _point("m1", 8, "player_b", "player_a"),
        ]
    }
    assert tour_average_serve_rate(matches, points, date(2026, 2, 1)) == 0.5


def test_tour_average_raises_when_no_prior_data():
    with pytest.raises(ValueError):
        tour_average_serve_rate([], {}, date(2026, 1, 1))


def test_tour_average_respects_no_look_ahead():
    matches = [
        _match("m1", date(2026, 1, 1), A, B),  # before cutoff
        _match("m2", date(2026, 1, 10), A, B),  # after cutoff — must not count
    ]
    points = {
        "m1": [_point("m1", 1, "player_a", "player_a")],  # 1/1 win
        "m2": [_point("m2", 1, "player_a", "player_b")],  # 0/1 win, must be excluded
    }
    assert tour_average_serve_rate(matches, points, date(2026, 1, 5)) == 1.0


def test_player_serve_rate_none_with_no_prior_service_points():
    assert player_serve_rate(A, [], {}, date(2026, 1, 1)) is None


def test_player_serve_rate_only_counts_that_players_own_serves():
    matches = [_match("m1", date(2026, 1, 1), A, B)]
    points = {
        "m1": [
            _point("m1", 1, "player_a", "player_a"),  # A serves, A wins
            _point("m1", 2, "player_a", "player_b"),  # A serves, A loses
            _point("m1", 3, "player_b", "player_b"),  # B serves — not A's data
        ]
    }
    assert player_serve_rate(A, matches, points, date(2026, 2, 1)) == 0.5


def test_shrinkage_returns_exactly_tour_average_for_a_player_with_no_data():
    matches = [_match("m1", date(2026, 1, 1), A, B)]
    points = {"m1": [_point("m1", 1, "player_a", "player_a")]}  # A: 1/1, tour avg = 1.0
    rate = serve_rate_with_shrinkage(C, matches, points, date(2026, 2, 1))
    assert rate == pytest.approx(1.0)


def test_shrinkage_pulls_a_small_sample_toward_the_tour_average():
    # Player A: 1 point served, lost it (0/1 -> empirical rate 0.0). A
    # large pool of unrelated matches sets a high tour average.
    matches = [
        _match("m1", date(2026, 1, 1), A, B),
        *[_match(f"m{i}", date(2026, 1, 1), "x", "y") for i in range(2, 22)],
    ]
    points = {"m1": [_point("m1", 1, "player_a", "player_b")]}  # A loses their one service point
    for i in range(2, 22):
        points[f"m{i}"] = [_point(f"m{i}", 1, "player_a", "player_a")]  # x holds serve

    tour_avg = tour_average_serve_rate(matches, points, date(2026, 2, 1))
    rate = serve_rate_with_shrinkage(A, matches, points, date(2026, 2, 1))
    # With only 1 real data point against a strength-20 prior, the estimate
    # should sit far closer to the tour average than to A's raw 0.0.
    assert 0.0 < rate < tour_avg
    assert rate > tour_avg / 2


def test_shrinkage_converges_to_empirical_rate_with_zero_strength():
    matches = [_match("m1", date(2026, 1, 1), A, B)]
    points = {
        "m1": [
            _point("m1", 1, "player_a", "player_a"),
            _point("m1", 2, "player_a", "player_a"),
            _point("m1", 3, "player_a", "player_b"),
        ]
    }
    rate = serve_rate_with_shrinkage(A, matches, points, date(2026, 2, 1), shrinkage_strength=0)
    assert rate == pytest.approx(2 / 3)


def test_default_shrinkage_strength_is_positive():
    assert DEFAULT_SHRINKAGE_STRENGTH > 0
