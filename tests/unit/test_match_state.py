from database.models import Point
from backend.match_state import compute_break_point, game_score_before, is_break_point


def _point(point_no, game_no, server, winner):
    return Point(
        match_id="m1",
        point_no=point_no,
        set_no=1,
        game_no=game_no,
        server=server,
        point_winner=winner,
        sets_won_a=0,
        sets_won_b=0,
        games_won_a=0,
        games_won_b=0,
        point_score="n/a",
    )


def test_is_break_point_true_when_receiver_one_point_away():
    assert is_break_point(receiver_points=3, server_points=0) is True  # 0-40
    assert is_break_point(receiver_points=4, server_points=3) is True  # Ad-receiver


def test_is_break_point_false_at_deuce_or_when_server_ahead():
    assert is_break_point(receiver_points=3, server_points=3) is False  # deuce
    assert is_break_point(receiver_points=1, server_points=3) is False  # 40-15 server ahead


def test_game_score_before_only_counts_earlier_points_in_the_same_game():
    points = [
        _point(1, 1, "player_a", "player_b"),
        _point(2, 1, "player_a", "player_b"),
        _point(3, 1, "player_a", "player_b"),
        _point(4, 2, "player_b", "player_a"),  # different game — should not count
    ]
    target = _point(4, 1, "player_a", "player_a")  # hypothetical 4th point of game 1
    won_a, won_b = game_score_before(points, target)
    assert (won_a, won_b) == (0, 3)


def test_compute_break_point_end_to_end():
    # player_a serves; player_b wins the first three points -> 0-40, a break point.
    points = [
        _point(1, 1, "player_a", "player_b"),
        _point(2, 1, "player_a", "player_b"),
        _point(3, 1, "player_a", "player_b"),
    ]
    target = _point(4, 1, "player_a", "player_a")
    assert compute_break_point(points, target) is True


def test_compute_break_point_false_when_server_has_the_advantage():
    points = [
        _point(1, 1, "player_a", "player_a"),
        _point(2, 1, "player_a", "player_a"),
        _point(3, 1, "player_a", "player_a"),
    ]
    target = _point(4, 1, "player_a", "player_a")
    assert compute_break_point(points, target) is False
