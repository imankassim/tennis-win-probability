from datetime import date

from database.ingestion.outcomes import derive_outcome
from database.models import Match, OutcomeLabel, Point, QuarantinedMatch

MATCH = Match(
    match_id="m1",
    tournament="Test Open",
    round="F",
    surface="hard",
    best_of=3,
    match_date=date(2026, 1, 1),
    player_a_id="player_a",
    player_b_id="player_b",
    source="test",
)


def _point(point_no, game_no, server, winner, sets_a, sets_b, games_a, games_b):
    return Point(
        match_id="m1",
        point_no=point_no,
        set_no=sets_a + sets_b + 1,
        game_no=game_no,
        server=server,
        point_winner=winner,
        sets_won_a=sets_a,
        sets_won_b=sets_b,
        games_won_a=games_a,
        games_won_b=games_b,
        point_score="n/a",
    )


def test_no_points_is_quarantined():
    result = derive_outcome(MATCH, [])
    assert isinstance(result, QuarantinedMatch)
    assert result.match_id == "m1"


def test_clean_straight_sets_win():
    # Player A already won set 1. In set 2, at 5-4 games (A leading),
    # A wins the last two points of the final game to close it 6-4 and
    # win the match 2-0.
    points = [
        _point(1, 10, "player_a", "player_a", sets_a=1, sets_b=0, games_a=5, games_b=4),
        _point(2, 10, "player_b", "player_a", sets_a=1, sets_b=0, games_a=5, games_b=4),
    ]
    result = derive_outcome(MATCH, points)
    assert result == OutcomeLabel(match_id="m1", actual_winner="player_a", final_score="2-0")


def test_tiebreak_win_completes_set_and_match():
    # Player B already has 1 set. Second set reaches 6-6, and B wins the
    # tiebreak game outright — that always completes the set, regardless
    # of the internal tiebreak score, which derive_outcome never inspects.
    points = [
        _point(1, 12, "player_a", "player_b", sets_a=0, sets_b=1, games_a=6, games_b=6),
        _point(2, 12, "player_b", "player_b", sets_a=0, sets_b=1, games_a=6, games_b=6),
    ]
    result = derive_outcome(MATCH, points)
    assert result == OutcomeLabel(match_id="m1", actual_winner="player_b", final_score="2-0")


def test_chart_stopping_mid_game_is_quarantined():
    # Last recorded point wins a point but the game isn't actually over
    # (games only reach 3-4, nowhere near a set).
    points = [
        _point(1, 8, "player_a", "player_b", sets_a=0, sets_b=0, games_a=3, games_b=4),
    ]
    result = derive_outcome(MATCH, points)
    assert isinstance(result, QuarantinedMatch)
    assert "does not complete a set" in result.reason


def test_chart_completing_a_set_but_not_the_match_is_quarantined():
    # Best of 3: winning this final game only brings the winner to 1 set,
    # short of the 2 needed to win the match.
    points = [
        _point(1, 10, "player_a", "player_a", sets_a=0, sets_b=0, games_a=5, games_b=3),
    ]
    result = derive_outcome(MATCH, points)
    assert isinstance(result, QuarantinedMatch)
    assert "not the match" in result.reason
