from datetime import date

from backend.context_features import head_to_head, recent_form, surface_record
from database.models import Match, OutcomeLabel

A, B, C = "player_a_id", "player_b_id", "player_c_id"


def _match(match_id, d, p1, p2, surface="hard"):
    return Match(
        match_id=match_id,
        tournament="t",
        round="F",
        surface=surface,
        best_of=3,
        match_date=d,
        player_a_id=p1,
        player_b_id=p2,
        source="test",
    )


def _win(match_id, winner_side):
    return OutcomeLabel(match_id=match_id, actual_winner=winner_side, final_score="2-0")


def test_recent_form_none_with_no_prior_matches():
    assert recent_form(A, [], {}, date(2026, 1, 1)) is None


def test_recent_form_computes_win_rate_over_lookback():
    matches = [
        _match("m1", date(2026, 1, 1), A, B),
        _match("m2", date(2026, 1, 2), A, B),
        _match("m3", date(2026, 1, 3), A, B),
    ]
    outcomes = {
        "m1": _win("m1", "player_a"),  # A wins (A is player_a in the match)
        "m2": _win("m2", "player_b"),  # A loses
        "m3": _win("m3", "player_a"),  # A wins
    }
    form = recent_form(A, matches, outcomes, date(2026, 1, 10), lookback=10)
    assert form == 2 / 3


def test_recent_form_never_sees_matches_on_or_after_as_of_date():
    matches = [
        _match("m1", date(2026, 1, 1), A, B),  # A loses — before cutoff, counts
        _match("m2", date(2026, 1, 5), A, B),  # A wins — on cutoff date, must NOT count
        _match("m3", date(2026, 1, 6), A, B),  # A wins — after cutoff, must NOT count
    ]
    outcomes = {
        "m1": _win("m1", "player_b"),
        "m2": _win("m2", "player_a"),
        "m3": _win("m3", "player_a"),
    }
    form = recent_form(A, matches, outcomes, as_of_date=date(2026, 1, 5))
    assert form == 0.0  # only m1 (a loss) is visible


def test_recent_form_respects_lookback_window():
    matches = [_match(f"m{i}", date(2026, 1, i + 1), A, B) for i in range(5)]
    # A loses the first 3, wins the last 2.
    outcomes = {
        "m0": _win("m0", "player_b"),
        "m1": _win("m1", "player_b"),
        "m2": _win("m2", "player_b"),
        "m3": _win("m3", "player_a"),
        "m4": _win("m4", "player_a"),
    }
    form = recent_form(A, matches, outcomes, date(2026, 2, 1), lookback=2)
    assert form == 1.0  # only the most recent 2 (both wins) count


def test_surface_record_filters_by_surface_and_excludes_unresolved():
    matches = [
        _match("m1", date(2026, 1, 1), A, B, surface="clay"),
        _match("m2", date(2026, 1, 2), A, B, surface="hard"),
        _match("m3", date(2026, 1, 3), A, B, surface="clay"),
    ]
    outcomes = {
        "m1": _win("m1", "player_a"),
        "m2": _win("m2", "player_a"),
        # m3 has no outcome (e.g. quarantined as incomplete) — excluded
    }
    wins, losses = surface_record(A, "clay", matches, outcomes, date(2026, 2, 1))
    assert (wins, losses) == (1, 0)


def test_head_to_head_only_counts_matches_between_exactly_these_two():
    matches = [
        _match("m1", date(2026, 1, 1), A, B),
        _match("m2", date(2026, 1, 2), A, C),  # not a match between A and B
        _match("m3", date(2026, 1, 3), B, A),  # order reversed, still A vs B
    ]
    outcomes = {
        "m1": _win("m1", "player_a"),  # A wins
        "m2": _win("m2", "player_a"),  # irrelevant to A-vs-B h2h
        "m3": _win("m3", "player_b"),  # player_b in this match is A -> A wins again
    }
    wins_a, wins_b = head_to_head(A, B, matches, outcomes, date(2026, 2, 1))
    assert (wins_a, wins_b) == (2, 0)
