import math

import pytest

from evaluation.metrics import brier_score, log_loss, percentile


def test_brier_score_is_zero_for_perfect_predictions():
    assert brier_score([1.0, 0.0, 1.0], [1.0, 0.0, 1.0]) == 0.0


def test_brier_score_for_always_fifty_fifty_on_balanced_outcomes():
    # EXP1's known, fixed score on a perfectly balanced field.
    assert brier_score([0.5, 0.5, 0.5, 0.5], [1.0, 0.0, 1.0, 0.0]) == 0.25


def test_brier_score_penalises_confident_wrong_predictions():
    confident_wrong = brier_score([0.9], [0.0])
    unsure = brier_score([0.5], [0.0])
    assert confident_wrong > unsure


def test_brier_score_rejects_mismatched_lengths():
    with pytest.raises(ValueError):
        brier_score([0.5, 0.5], [1.0])


def test_brier_score_rejects_empty_input():
    with pytest.raises(ValueError):
        brier_score([], [])


def test_log_loss_is_zero_for_perfect_confident_predictions():
    assert log_loss([1.0, 0.0], [1.0, 0.0]) == pytest.approx(0.0, abs=1e-9)


def test_log_loss_for_always_fifty_fifty_is_ln2():
    assert log_loss([0.5, 0.5], [1.0, 0.0]) == pytest.approx(math.log(2))


def test_log_loss_does_not_blow_up_on_a_confident_wrong_prediction():
    # Without clipping this would be -log(0) = inf.
    result = log_loss([1.0], [0.0])
    assert math.isfinite(result)
    assert result > 30  # still a very large penalty


def test_log_loss_penalises_confident_wrong_more_than_log_loss_of_unsure():
    confident_wrong = log_loss([0.99], [0.0])
    unsure = log_loss([0.5], [0.0])
    assert confident_wrong > unsure


def test_percentile_median_of_odd_length_list():
    assert percentile([1, 2, 3, 4, 5], 50) == 3


def test_percentile_p95_of_a_larger_list():
    values = list(range(1, 101))  # 1..100
    assert percentile(values, 95) == 95


def test_percentile_rejects_out_of_range_pct():
    with pytest.raises(ValueError):
        percentile([1, 2, 3], 150)


def test_percentile_rejects_empty_list():
    with pytest.raises(ValueError):
        percentile([], 50)
