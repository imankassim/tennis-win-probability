"""Latency reporting (Journey 8) from the quote event log (Journey 7)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from backend.event_log import read_quote_log
from evaluation.metrics import percentile


@dataclass(frozen=True)
class LatencyReport:
    n: int
    median_ms: float
    p95_ms: float


def report_latency(path: Path | None = None) -> LatencyReport:
    records = read_quote_log(path)
    if not records:
        raise ValueError("no quote log records to report on")
    latencies = [r["latency_ms"] for r in records]
    return LatencyReport(
        n=len(latencies),
        median_ms=percentile(latencies, 50),
        p95_ms=percentile(latencies, 95),
    )
