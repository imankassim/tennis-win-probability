from pricing.baselines.heuristics import always_fifty_fifty, score_leader_probability


def test_always_fifty_fifty_ignores_all_state():
    assert always_fifty_fifty() == 0.5


def test_score_leader_tied_match_is_fifty_fifty():
    assert score_leader_probability(sets_a=0, sets_b=0, games_a=0, games_b=0) == 0.5
    assert score_leader_probability(sets_a=1, sets_b=1, games_a=3, games_b=3) == 0.5


def test_score_leader_set_lead_dominates_game_state():
    # A trails on games in the current set but leads on sets overall.
    assert score_leader_probability(sets_a=1, sets_b=0, games_a=1, games_b=4) == 0.75
    assert score_leader_probability(sets_a=0, sets_b=1, games_a=4, games_b=1) == 0.25


def test_score_leader_game_lead_within_a_tied_set():
    assert score_leader_probability(sets_a=0, sets_b=0, games_a=4, games_b=2) == 0.6
    assert score_leader_probability(sets_a=0, sets_b=0, games_a=2, games_b=4) == 0.4


def test_score_leader_is_symmetric():
    """Swapping both players' figures should mirror the probability around 0.5."""
    p_a = score_leader_probability(sets_a=1, sets_b=0, games_a=3, games_b=5)
    p_b = score_leader_probability(sets_a=0, sets_b=1, games_a=5, games_b=3)
    assert p_a == 1 - p_b
