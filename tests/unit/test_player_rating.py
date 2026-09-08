from datetime import date

import pytest

from backend.player_rating import (
    DEFAULT_RATING,
    compute_rating_history,
    rating_as_of,
)
from database.models import Match, OutcomeLabel

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


def _win(match_id, winner_side):
    return OutcomeLabel(match_id=match_id, actual_winner=winner_side, final_score="2-0")


def test_unrated_player_gets_the_default_rating():
    history = compute_rating_history([], {})
    assert rating_as_of(A, history, date(2026, 1, 1)) == DEFAULT_RATING


def test_winner_gains_rating_and_loser_loses_it():
    matches = [_match("m1", date(2026, 1, 1), A, B)]
    outcomes = {"m1": _win("m1", "player_a")}
    history = compute_rating_history(matches, outcomes)

    a_after = rating_as_of(A, history, date(2026, 1, 2))
    b_after = rating_as_of(B, history, date(2026, 1, 2))
    assert a_after > DEFAULT_RATING
    assert b_after < DEFAULT_RATING


def test_rating_changes_are_zero_sum_between_evenly_matched_players():
    matches = [_match("m1", date(2026, 1, 1), A, B)]
    outcomes = {"m1": _win("m1", "player_a")}
    history = compute_rating_history(matches, outcomes)

    a_after = rating_as_of(A, history, date(2026, 1, 2))
    b_after = rating_as_of(B, history, date(2026, 1, 2))
    assert (a_after - DEFAULT_RATING) == pytest.approx(-(b_after - DEFAULT_RATING))


def test_beating_a_higher_rated_opponent_gains_more_than_beating_a_lower_rated_one():
    # First, build up player C as a strong player by beating several
    # opponents, then compare A's gain from beating C vs beating a fresh,
    # unrated opponent B.
    matches = [
        _match("c1", date(2026, 1, 1), C, "x1"),
        _match("c2", date(2026, 1, 2), C, "x2"),
        _match("c3", date(2026, 1, 3), C, "x3"),
    ]
    outcomes = {
        "c1": _win("c1", "player_a"),
        "c2": _win("c2", "player_a"),
        "c3": _win("c3", "player_a"),
    }
    history = compute_rating_history(matches, outcomes)
    c_rating = rating_as_of(C, history, date(2026, 1, 10))
    assert c_rating > DEFAULT_RATING

    # Now: A beats C (the now-strong player) vs A beats a fresh player B.
    matches_beat_strong = matches + [_match("m1", date(2026, 1, 10), A, C)]
    outcomes_beat_strong = dict(outcomes, m1=_win("m1", "player_a"))
    history_strong = compute_rating_history(matches_beat_strong, outcomes_beat_strong)
    a_gain_vs_strong = rating_as_of(A, history_strong, date(2026, 1, 11)) - DEFAULT_RATING

    matches_beat_fresh = [_match("m2", date(2026, 1, 10), A, B)]
    outcomes_beat_fresh = {"m2": _win("m2", "player_a")}
    history_fresh = compute_rating_history(matches_beat_fresh, outcomes_beat_fresh)
    a_gain_vs_fresh = rating_as_of(A, history_fresh, date(2026, 1, 11)) - DEFAULT_RATING

    assert a_gain_vs_strong > a_gain_vs_fresh


def test_rating_as_of_respects_no_look_ahead():
    matches = [
        _match("m1", date(2026, 1, 1), A, B),
        _match("m2", date(2026, 1, 10), A, B),
    ]
    outcomes = {"m1": _win("m1", "player_a"), "m2": _win("m2", "player_a")}
    history = compute_rating_history(matches, outcomes)

    # Querying for a date between the two matches should reflect only m1.
    rating_mid = rating_as_of(A, history, date(2026, 1, 5))
    rating_after_both = rating_as_of(A, history, date(2026, 1, 11))
    assert rating_mid < rating_after_both

    # Querying on m2's own date must not include m2 itself.
    rating_on_m2_date = rating_as_of(A, history, date(2026, 1, 10))
    assert rating_on_m2_date == rating_mid


def test_matches_without_a_confirmed_outcome_are_excluded():
    matches = [_match("m1", date(2026, 1, 1), A, B)]
    history = compute_rating_history(matches, outcomes={})
    assert rating_as_of(A, history, date(2026, 1, 2)) == DEFAULT_RATING
