"""Data quality gates (docs/architecture/data-architecture.md, section 8.3).

Pure functions over already-parsed records — no database, no network — so
they can be unit tested with small synthetic fixtures and reused
identically whatever the ingestion source turns out to be next.

Two of the eight documented gates aren't implemented here because they
don't apply to match/player/point ingestion:
- "Probability values within [0, 1] and prices >= 1.0, or null while
  suspended" belongs to the quote pipeline (Journey 5+).
- "Model version tied to the source data snapshot" belongs to model
  training (Journey 9+).
A third — "outcome labels consistent with the final recorded score" — is
enforced by construction in outcomes.py: derive_outcome() only ever
returns a label when it has confirmed the match-ending point, and
quarantines the match otherwise.
"""

from __future__ import annotations

from database.models import Match, Point

VALID_SERVER_VALUES = {"player_a", "player_b"}


def check_unique_nonnull_match_ids(matches: list[Match]) -> list[str]:
    violations = []
    seen: set[str] = set()
    for m in matches:
        if not m.match_id:
            violations.append("match with a null/empty match_id")
            continue
        if m.match_id in seen:
            violations.append(f"duplicate match_id {m.match_id!r}")
        seen.add(m.match_id)
    return violations


def check_unique_nonnull_point_ids(points: list[Point]) -> list[str]:
    violations = []
    seen: set[int] = set()
    for p in points:
        if p.point_no is None:
            violations.append("point with a null point_no")
            continue
        if p.point_no in seen:
            violations.append(f"duplicate point_no {p.point_no}")
        seen.add(p.point_no)
    return violations


def check_monotonic_point_sequence(points: list[Point]) -> list[str]:
    violations = []
    for prev, cur in zip(points, points[1:]):
        if cur.point_no <= prev.point_no:
            violations.append(
                f"point sequence not increasing: {prev.point_no} -> {cur.point_no}"
            )
    return violations


def check_valid_server(points: list[Point]) -> list[str]:
    return [
        f"point {p.point_no} has an invalid server value: {p.server!r}"
        for p in points
        if p.server not in VALID_SERVER_VALUES
    ]


def check_no_duplicate_points(points: list[Point]) -> list[str]:
    seen: set[int] = set()
    violations = []
    for p in points:
        if p.point_no in seen:
            violations.append(f"point_no {p.point_no} appears more than once")
        seen.add(p.point_no)
    return violations


def validate_match_points(points: list[Point]) -> list[str]:
    """Runs every gate against one match's points, in source (point_no) order."""
    violations: list[str] = []
    violations += check_unique_nonnull_point_ids(points)
    violations += check_monotonic_point_sequence(points)
    violations += check_valid_server(points)
    violations += check_no_duplicate_points(points)
    return violations
