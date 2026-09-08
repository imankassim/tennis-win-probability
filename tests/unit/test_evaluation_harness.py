from datetime import date

import pytest

from database.models import Match, OutcomeLabel, Point
from evaluation.harness import evaluate_configuration


def _match(match_id):
    return Match(
        match_id=match_id,
        tournament="t",
        round="F",
        surface="hard",
        best_of=3,
        match_date=date(2026, 1, 1),
        player_a_id="a",
        player_b_id="b",
        source="test",
    )


def _point(match_id, point_no, sets_a=0, sets_b=0, games_a=0, games_b=0):
    return Point(
        match_id=match_id,
        point_no=point_no,
        set_no=1,
        game_no=1,
        server="player_a",
        point_winner="player_a",
        sets_won_a=sets_a,
        sets_won_b=sets_b,
        games_won_a=games_a,
        games_won_b=games_b,
        point_score="n/a",
    )


def test_evaluate_configuration_scores_a_perfect_predictor():
    matches = [_match("m1")]
    points_by_match = {"m1": [_point("m1", 1), _point("m1", 2)]}
    outcomes = {"m1": OutcomeLabel(match_id="m1", actual_winner="player_a", final_score="2-0")}

    result = evaluate_configuration(
        "always_correct",
        lambda sa, sb, ga, gb: 1.0,
        matches,
        points_by_match,
        outcomes,
    )
    assert result.brier == 0.0
    assert result.n_points == 2
    assert result.n_matches == 1


def test_evaluate_configuration_excludes_matches_without_a_confirmed_outcome():
    matches = [_match("m1"), _match("m2")]
    points_by_match = {
        "m1": [_point("m1", 1)],
        "m2": [_point("m2", 1)],  # no outcome for m2 — should be excluded
    }
    outcomes = {"m1": OutcomeLabel(match_id="m1", actual_winner="player_a", final_score="2-0")}

    result = evaluate_configuration(
        "test", lambda sa, sb, ga, gb: 0.5, matches, points_by_match, outcomes
    )
    assert result.n_matches == 1
    assert result.n_points == 1


def test_evaluate_configuration_raises_when_nothing_is_evaluable():
    with pytest.raises(ValueError):
        evaluate_configuration("empty", lambda sa, sb, ga, gb: 0.5, [], {}, {})


def test_a_better_predictor_scores_a_lower_brier_than_a_worse_one():
    matches = [_match("m1")]
    # player_a is clearly ahead: 1 set, 5 games to 2.
    points_by_match = {"m1": [_point("m1", 1, sets_a=1, sets_b=0, games_a=5, games_b=2)]}
    outcomes = {"m1": OutcomeLabel(match_id="m1", actual_winner="player_a", final_score="2-0")}

    from pricing.baselines.heuristics import always_fifty_fifty, score_leader_probability

    always_result = evaluate_configuration(
        "always_50_50",
        lambda sa, sb, ga, gb: always_fifty_fifty(),
        matches,
        points_by_match,
        outcomes,
    )
    leader_result = evaluate_configuration(
        "score_leader",
        lambda sa, sb, ga, gb: score_leader_probability(sa, sb, ga, gb),
        matches,
        points_by_match,
        outcomes,
    )
    assert leader_result.brier < always_result.brier
