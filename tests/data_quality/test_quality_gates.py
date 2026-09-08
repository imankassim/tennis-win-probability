from database.models import Match, Point
from database.quality_gates import (
    check_monotonic_point_sequence,
    check_no_duplicate_points,
    check_unique_nonnull_match_ids,
    check_valid_server,
    validate_match_points,
)


def _point(point_no, server="player_a", winner="player_a"):
    return Point(
        match_id="m1",
        point_no=point_no,
        set_no=1,
        game_no=1,
        server=server,
        point_winner=winner,
        sets_won_a=0,
        sets_won_b=0,
        games_won_a=0,
        games_won_b=0,
        point_score="0-0",
    )


def _match(match_id):
    return Match(
        match_id=match_id,
        tournament="t",
        round="F",
        surface="hard",
        best_of=3,
        match_date=None,
        player_a_id="a",
        player_b_id="b",
        source="test",
    )


def test_clean_points_pass_every_gate():
    points = [_point(1), _point(2), _point(3)]
    assert validate_match_points(points) == []


def test_duplicate_point_no_is_caught():
    points = [_point(1), _point(2), _point(2)]
    violations = check_no_duplicate_points(points)
    assert len(violations) == 1
    assert "2" in violations[0]


def test_non_monotonic_sequence_is_caught():
    points = [_point(1), _point(3), _point(2)]
    violations = check_monotonic_point_sequence(points)
    assert len(violations) == 1


def test_invalid_server_value_is_caught():
    points = [_point(1, server="player_a"), _point(2, server="bogus")]
    violations = check_valid_server(points)
    assert len(violations) == 1
    assert "bogus" in violations[0]


def test_duplicate_match_ids_are_caught():
    matches = [_match("m1"), _match("m2"), _match("m1")]
    violations = check_unique_nonnull_match_ids(matches)
    assert len(violations) == 1
    assert "m1" in violations[0]


def test_null_match_id_is_caught():
    matches = [_match("")]
    violations = check_unique_nonnull_match_ids(matches)
    assert len(violations) == 1
