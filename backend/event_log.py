"""Quote event logging (Journey 7 — instrumentation).

Combines the two related data-architecture entities into one record per
served quote, rather than two separate files — practical for a
prototype-scale analytical store, and exactly what
docs/architecture/data-architecture.md allows ("Analytical store or files
... Not responsible for serving live probability requests directly"):

- "Probability request (quote)": probability_request_id, match_id,
  point_sequence, model_version, latency, fallback_used.
- "Quote event": event_id, type, probability_request_id, timestamp.

No personal data is logged — only match/point/model identifiers and
timing, consistent with FR-05 ("quote and replay events can be recorded
without collecting unnecessary personal data").

The log is a plain append-only JSONL file — deliberately not a database,
matching the storage responsibility split (PostgreSQL is not responsible
for quote logs; an "analytical store or files" is). Journey 8's evaluation
harness reads this file directly.
"""

from __future__ import annotations

import itertools
import json
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from backend.schemas import ProbabilityResponse

DEFAULT_LOG_PATH = Path("data/quote_log.jsonl")

_event_ids = itertools.count(1)


@dataclass(frozen=True)
class QuoteLogRecord:
    event_id: str
    type: str
    timestamp: float
    probability_request_id: str
    match_id: str
    point_sequence: int
    model_version: str
    latency_ms: float
    fallback_used: bool
    suspended: bool


def _log_path() -> Path:
    return Path(os.environ.get("COURTEDGE_QUOTE_LOG_PATH", DEFAULT_LOG_PATH))


def build_record(response: ProbabilityResponse, latency_ms: float) -> QuoteLogRecord:
    return QuoteLogRecord(
        event_id=f"evt_{next(_event_ids):x}",
        type="quote_served",
        timestamp=time.time(),
        probability_request_id=response.probability_request_id,
        match_id=response.match_id,
        point_sequence=response.point_sequence,
        model_version=response.model_version,
        latency_ms=round(latency_ms, 3),
        fallback_used=response.fallback_used,
        suspended=response.suspended,
    )


def log_quote(response: ProbabilityResponse, latency_ms: float, path: Path | None = None) -> None:
    record = build_record(response, latency_ms)
    target = path if path is not None else _log_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(record)) + "\n")


def read_quote_log(path: Path | None = None) -> list[dict]:
    target = path if path is not None else _log_path()
    if not target.exists():
        return []
    with target.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]
