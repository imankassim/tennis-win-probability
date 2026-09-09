from datetime import date

from database.models import Match, OutcomeLabel, Point
from pricing.ml.features import build_point_features, compute_match_context_features

A, B, C = "player_a_id", "player_b_id", "player_c_id"


def _match(match_id, d, p1, p2, surface="hard", best_of=3):
    return Match(
        match_id=match_id,
        tournament="t",
        round="F",
        surface=surface,
        best_of=best_of,
        match_date=d,
        player_a_id=p1,
        player_b_id=p2,
        source="test",
    )


def _win(match_id, side):
    return OutcomeLabel(match_id=match_id, actual_winner=side, final_score="2-0")


def _point(match_id, point_no, server="player_a", winner="player_a", sa=0, sb=0, ga=0, gb=0):
    return Point(
        match_id=match_id,
        point_no=point_no,
        set_no=1,
        game_no=1,
        server=server,
        point_winner=winner,
        sets_won_a=sa,
        sets_won_b=sb,
        games_won_a=ga,
        games_won_b=gb,
        point_score="n/a",
    )


def test_context_features_default_neutral_for_debut_players():
    matches = [_match("m1", date(2026, 1, 1), A, B)]
    outcomes = {"m1": _win("m1", "player_a")}
    ctx = compute_match_context_features(matches, outcomes)
    assert ctx["m1"]["form_a"] == 0.5
    assert ctx["m1"]["form_b"] == 0.5
    assert ctx["m1"]["h2h_rate_a"] == 0.5
    assert ctx["m1"]["elo_a"] == 1500.0


def test_context_features_respect_no_look_ahead():
    matches = [
        _match("m1", date(2026, 1, 1), A, B),
        _match("m2", date(2026, 1, 10), A, B),
    ]
    outcomes = {"m1": _win("m1", "player_a"), "m2": _win("m2", "player_a")}
    ctx = compute_match_context_features(matches, outcomes)
    # m1 is the first meeting - no history yet.
    assert ctx["m1"]["form_a"] == 0.5
    assert ctx["m1"]["h2h_rate_a"] == 0.5
    # m2 sees m1's result: A won, so A's form/h2h/elo should all have moved up.
    assert ctx["m2"]["form_a"] == 1.0
    assert ctx["m2"]["h2h_rate_a"] == 1.0
    assert ctx["m2"]["elo_a"] > 1500.0


def test_context_features_track_surface_separately():
    matches = [
        _match("m1", date(2026, 1, 1), A, B, surface="clay"),
        _match("m2", date(2026, 1, 10), A, C, surface="hard"),
    ]
    outcomes = {"m1": _win("m1", "player_a"), "m2": _win("m2", "player_a")}
    ctx = compute_match_context_features(matches, outcomes)
    # m2 is on a different surface from m1 - A's surface record there is still blank.
    assert ctx["m2"]["surface_rate_a"] == 0.5


def test_build_point_features_labels_and_state_columns():
    matches = [_match("m1", date(2026, 1, 1), A, B, best_of=3)]
    outcomes = {"m1": _win("m1", "player_a")}
    points_by_match = {
        "m1": [
            _point("m1", 1, server="player_a", winner="player_a", sa=0, sb=0, ga=0, gb=0),
            _point("m1", 2, server="player_a", winner="player_b", sa=0, sb=0, ga=0, gb=0),
        ]
    }
    ctx = compute_match_context_features(matches, outcomes)
    df = build_point_features(matches, points_by_match, outcomes, ctx)

    assert len(df) == 2
    assert (df["label"] == 1).all()  # player_a won the match
    assert (df["best_of"] == 3).all()
    assert df.iloc[0]["server_is_a"] == 1


def test_build_point_features_momentum_reflects_recent_points_within_match():
    matches = [_match("m1", date(2026, 1, 1), A, B)]
    outcomes = {"m1": _win("m1", "player_a")}
    points_by_match = {
        "m1": [
            _point("m1", 1, winner="player_a"),
            _point("m1", 2, winner="player_a"),
            _point("m1", 3, winner="player_b"),
        ]
    }
    ctx = compute_match_context_features(matches, outcomes)
    df = build_point_features(matches, points_by_match, outcomes, ctx)

    # First point: no prior points this match -> neutral momentum.
    assert df.iloc[0]["momentum_a"] == 0.5
    # Third point: prior points in this match were A, A -> momentum 1.0.
    assert df.iloc[2]["momentum_a"] == 1.0


def test_build_point_features_excludes_matches_without_a_confirmed_outcome():
    matches = [_match("m1", date(2026, 1, 1), A, B)]
    points_by_match = {"m1": [_point("m1", 1)]}
    df = build_point_features(matches, points_by_match, outcomes={}, match_context={})
    assert len(df) == 0
