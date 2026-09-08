import pytest

from trading_rules.rules import (
    DEFAULT_MARGIN,
    MAX_REASONABLE_PRICE,
    WIDENED_MARGIN,
    apply_trading_rules,
    is_stale,
    price_from_probability,
)


def test_price_from_probability_applies_margin():
    # At p=0.5 with no margin, fair price is 2.0; a 5% margin shortens it.
    assert price_from_probability(0.5, margin=0.0) == 2.0
    assert price_from_probability(0.5, margin=0.05) < 2.0


def test_widened_margin_produces_shorter_prices_than_the_default():
    """The margin backend/probability.py requests when blend/calibration
    fails after a successful ML estimate (docs/architecture/deployment.md's
    "blend or calibration unavailable" row) — must be strictly more
    conservative than the default, or widening it would be pointless."""
    assert WIDENED_MARGIN > DEFAULT_MARGIN
    default_result = apply_trading_rules(0.6, margin=DEFAULT_MARGIN)
    widened_result = apply_trading_rules(0.6, margin=WIDENED_MARGIN)
    assert widened_result.price_a < default_result.price_a
    assert widened_result.price_b < default_result.price_b


def test_apply_trading_rules_returns_valid_prices_for_a_normal_probability():
    result = apply_trading_rules(0.6)
    assert result.suspended is False
    assert result.reason is None
    assert result.price_a is not None and result.price_a >= 1.0
    assert result.price_b is not None and result.price_b >= 1.0
    # Prices should be roughly complementary (both sides overround by the margin).
    implied_a = 1 / result.price_a
    implied_b = 1 / result.price_b
    assert implied_a + implied_b > 1.0  # a book with margin overrounds


def test_apply_trading_rules_suspends_on_missing_probability():
    result = apply_trading_rules(None)
    assert result.suspended is True
    assert result.price_a is None
    assert result.price_b is None
    assert result.reason is not None


@pytest.mark.parametrize("bad_probability", [-0.1, 1.1, 0.0, 1.0])
def test_apply_trading_rules_suspends_on_invalid_or_unpriceable_probability(bad_probability):
    result = apply_trading_rules(bad_probability)
    assert result.suspended is True
    assert result.price_a is None
    assert result.price_b is None


def test_apply_trading_rules_suspends_rather_than_serving_an_absurd_price():
    # An extremely lopsided probability produces a price far past any
    # reasonable bound on one side - must suspend rather than serve it.
    result = apply_trading_rules(0.0001, margin=DEFAULT_MARGIN)
    assert result.suspended is True
    assert result.reason is not None


def test_apply_trading_rules_never_exceeds_the_reasonable_price_cap():
    for p in [0.001, 0.01, 0.5, 0.99, 0.999]:
        result = apply_trading_rules(p)
        if not result.suspended:
            assert result.price_a <= MAX_REASONABLE_PRICE
            assert result.price_b <= MAX_REASONABLE_PRICE


def test_is_stale_true_past_the_threshold():
    assert is_stale(data_age_seconds=45, max_age_seconds=30) is True


def test_is_stale_false_within_the_threshold():
    assert is_stale(data_age_seconds=10, max_age_seconds=30) is False


def test_is_stale_false_exactly_at_the_threshold():
    assert is_stale(data_age_seconds=30, max_age_seconds=30) is False
