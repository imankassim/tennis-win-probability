from datetime import date

import pytest

from database.models import Match, Point
from pricing.markov.engine import (
    COLD_START_SERVE_RATE,
    estimate_match_serve_rates,
    markov_probability,
)

A, B = "player_a_id", "player_b_id"


def _match(match_id, d, p1=A, p2=B):
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


def test_estimate_match_serve_rates_falls_back_to_cold_start_with_no_history():
    match = _match("m1", date(2026, 1, 1))
    p_a, p_b = estimate_match_serve_rates(match, [match], {"m1": []})
    assert p_a == COLD_START_SERVE_RATE
    assert p_b == COLD_START_SERVE_RATE


def test_estimate_match_serve_rates_uses_real_prior_history():
    earlier = _match("m0", date(2026, 1, 1))
    target = _match("m1", date(2026, 2, 1))
    points = {
        "m0": [_point("m0", 1, "player_a", "player_a"), _point("m0", 2, "player_a", "player_a")],
        "m1": [],
    }
    p_a, p_b = estimate_match_serve_rates(target, [earlier, target], points)
    assert p_a > COLD_START_SERVE_RATE  # A held serve both points before this match


def test_markov_probability_matches_the_underlying_formula_directly():
    from pricing.markov.formulas import prob_win_match

    expected = prob_win_match(0.65, 0.55, 3, 1, 0, 3, 2, True, 0, 0)
    actual = markov_probability(0.65, 0.55, 3, 1, 0, 3, 2, "player_a")
    assert actual == pytest.approx(expected)


def test_markov_probability_respects_which_player_is_serving():
    # From a genuinely fresh 0-0 set, who serves first doesn't affect the
    # outcome (verified independently by Monte Carlo simulation — a real
    # property of alternating service, not a bug) — so this needs a
    # mid-match state to actually exercise server-dependence.
    p_a_serving = markov_probability(0.65, 0.55, 3, 0, 0, 3, 2, "player_a")
    p_b_serving = markov_probability(0.65, 0.55, 3, 0, 0, 3, 2, "player_b")
    assert p_a_serving > p_b_serving
