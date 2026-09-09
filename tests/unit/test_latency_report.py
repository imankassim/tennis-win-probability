import pytest

from backend.event_log import log_quote
from backend.schemas import MatchStateInterpretation, ProbabilityResponse
from evaluation.latency_report import report_latency


def _response():
    return ProbabilityResponse(
        probability_request_id="req_1",
        match_id="m1",
        point_sequence=1,
        interpretation=MatchStateInterpretation(
            set=1, games="0-0", server="player_a", break_point=False
        ),
        probability_player_a=0.5,
        price_player_a=1.9,
        price_player_b=1.9,
        model_version="test",
        fallback_used=False,
        suspended=False,
        markov_probability_a=0.5,
        ml_probability_a=None,
    )


def test_report_latency_computes_median_and_p95(tmp_path):
    log_path = tmp_path / "quotes.jsonl"
    for latency in [10, 20, 30, 40, 100]:
        log_quote(_response(), latency_ms=latency, path=log_path)

    report = report_latency(log_path)
    assert report.n == 5
    assert report.median_ms == 30
    assert report.p95_ms == 100


def test_report_latency_raises_when_log_is_empty(tmp_path):
    with pytest.raises(ValueError):
        report_latency(tmp_path / "does_not_exist.jsonl")
