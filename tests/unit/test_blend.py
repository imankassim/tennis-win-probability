import pytest

from pricing.blend.blend import blend_probability, tune_weight


def test_blend_probability_at_full_markov_weight_is_markov_only():
    assert blend_probability(markov_p=0.7, ml_p=0.3, markov_weight=1.0) == 0.7


def test_blend_probability_at_zero_markov_weight_is_ml_only():
    assert blend_probability(markov_p=0.7, ml_p=0.3, markov_weight=0.0) == 0.3


def test_blend_probability_at_half_weight_is_the_midpoint():
    assert blend_probability(markov_p=0.8, ml_p=0.4, markov_weight=0.5) == pytest.approx(0.6)


def test_blend_probability_rejects_out_of_range_weight():
    with pytest.raises(ValueError):
        blend_probability(0.5, 0.5, markov_weight=1.5)


def test_tune_weight_prefers_the_more_accurate_source():
    # ML predictions are perfect; Markov predictions are the opposite.
    # Tuning should land on markov_weight close to 0 (trust ML).
    markov_preds = [0.9, 0.9, 0.1, 0.1]
    ml_preds = [1.0, 1.0, 0.0, 0.0]
    actuals = [1.0, 1.0, 0.0, 0.0]

    best_weight, best_brier = tune_weight(markov_preds, ml_preds, actuals, step=0.1)
    assert best_weight <= 0.1
    assert best_brier < 0.01


def test_tune_weight_prefers_markov_when_it_is_the_accurate_source():
    markov_preds = [1.0, 1.0, 0.0, 0.0]
    ml_preds = [0.5, 0.5, 0.5, 0.5]
    actuals = [1.0, 1.0, 0.0, 0.0]

    best_weight, best_brier = tune_weight(markov_preds, ml_preds, actuals, step=0.1)
    assert best_weight >= 0.9
    assert best_brier < 0.01


def test_tune_weight_rejects_mismatched_lengths():
    with pytest.raises(ValueError):
        tune_weight([0.5, 0.5], [0.5], [1.0, 0.0])
