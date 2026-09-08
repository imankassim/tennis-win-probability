from backend.event_log import log_quote, read_quote_log
from backend.schemas import MatchStateInterpretation, ProbabilityResponse


def _response(**overrides):
    defaults = dict(
        probability_request_id="req_1",
        match_id="m1",
        point_sequence=5,
        interpretation=MatchStateInterpretation(
            set=1, games="2-1", server="player_a", break_point=False
        ),
        probability_player_a=0.6,
        price_player_a=1.7,
        price_player_b=2.4,
        model_version="score_leader_heuristic_v0",
        fallback_used=False,
        suspended=False,
    )
    defaults.update(overrides)
    return ProbabilityResponse(**defaults)


def test_log_quote_writes_one_jsonl_record(tmp_path):
    log_path = tmp_path / "quotes.jsonl"
    log_quote(_response(), latency_ms=12.5, path=log_path)

    records = read_quote_log(log_path)
    assert len(records) == 1
    record = records[0]
    assert record["type"] == "quote_served"
    assert record["probability_request_id"] == "req_1"
    assert record["match_id"] == "m1"
    assert record["point_sequence"] == 5
    assert record["model_version"] == "score_leader_heuristic_v0"
    assert record["latency_ms"] == 12.5
    assert record["fallback_used"] is False
    assert record["suspended"] is False
    assert "timestamp" in record and "event_id" in record


def test_log_quote_appends_across_calls(tmp_path):
    log_path = tmp_path / "quotes.jsonl"
    log_quote(_response(point_sequence=1), latency_ms=1.0, path=log_path)
    log_quote(_response(point_sequence=2), latency_ms=2.0, path=log_path)

    records = read_quote_log(log_path)
    assert [r["point_sequence"] for r in records] == [1, 2]
    # event IDs must be distinct even across calls
    assert records[0]["event_id"] != records[1]["event_id"]


def test_read_quote_log_returns_empty_list_when_file_is_missing(tmp_path):
    assert read_quote_log(tmp_path / "does_not_exist.jsonl") == []


def test_log_quote_creates_parent_directories(tmp_path):
    nested_path = tmp_path / "nested" / "dir" / "quotes.jsonl"
    log_quote(_response(), latency_ms=1.0, path=nested_path)
    assert nested_path.exists()
