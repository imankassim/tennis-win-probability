import pytest

from trading_rules.value_detection import (
    FLAG_THRESHOLD,
    MAX_REPORTED_EDGE,
    compute_value_flag,
    devig_odds,
)


def test_devig_odds_removes_the_overround():
    # Raw implied probabilities from odds 1.9/1.9 sum to > 1 (the margin).
    raw_sum = 1 / 1.9 + 1 / 1.9
    assert raw_sum > 1.0
    fair_a, fair_b = devig_odds(1.9, 1.9)
    assert fair_a + fair_b == pytest.approx(1.0)
    assert fair_a == pytest.approx(0.5)  # symmetric odds -> even fair split


def test_devig_odds_preserves_the_favourite_underdog_ordering():
    fair_a, fair_b = devig_odds(1.5, 2.8)  # A is the favourite (shorter odds)
    assert fair_a > fair_b


def test_devig_odds_rejects_odds_at_or_below_one():
    with pytest.raises(ValueError):
        devig_odds(1.0, 2.0)
    with pytest.raises(ValueError):
        devig_odds(0.9, 2.0)


def test_compute_value_flag_not_flagged_when_model_agrees_with_market():
    flag = compute_value_flag(model_probability=0.526, odds_a=1.9, odds_b=1.9)
    assert flag.flagged is False


def test_compute_value_flag_flagged_when_model_disagrees_meaningfully():
    # Market thinks ~50/50 (odds 1.9/1.9); model is confident in A.
    flag = compute_value_flag(model_probability=0.65, odds_a=1.9, odds_b=1.9)
    assert flag.flagged is True
    assert flag.edge > 0


def test_compute_value_flag_edge_is_capped():
    # An extreme, implausible disagreement should be capped, not reported raw.
    flag = compute_value_flag(model_probability=0.99, odds_a=1.9, odds_b=1.9)
    assert flag.edge == pytest.approx(MAX_REPORTED_EDGE)


def test_compute_value_flag_edge_is_capped_in_the_negative_direction_too():
    flag = compute_value_flag(model_probability=0.01, odds_a=1.9, odds_b=1.9)
    assert flag.edge == pytest.approx(-MAX_REPORTED_EDGE)


def test_flag_threshold_and_max_edge_are_consistent():
    # The cap must be at least as large as the flagging threshold, or a
    # capped edge could never actually trigger a flag.
    assert MAX_REPORTED_EDGE >= FLAG_THRESHOLD
