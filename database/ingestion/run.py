"""Ingestion entry point: parse Match Charting Project CSVs, run the data
quality gates, derive outcome labels, and report the result.

This does NOT write to PostgreSQL yet — no live database is assumed to be
available in every development environment. It produces the same validated
records a loader would insert, plus a quarantine report, so the pipeline is
fully exercisable and testable without a running database (consistent with
the offline/online separation principle: nothing here depends on the
serving path).

Usage:
    python -m database.ingestion.run <matches.csv> <points.csv> [<points2.csv> ...]

Multiple points files are accepted (e.g. the Match Charting Project's
separate per-decade files) and merged — real match_ids never repeat
across them, since each decade file only contains matches from that
decade.

The source CSVs are never committed to the repository — see
docs/data_sheets/data_provenance.md. Download them yourself:
https://github.com/JeffSackmann/tennis_MatchChartingProject
"""

from __future__ import annotations

import sys
from pathlib import Path

from database.ingestion.match_charting_project import parse_matches, parse_points_by_match
from database.ingestion.outcomes import derive_outcome
from database.models import Match, OutcomeLabel, Player, Point, QuarantinedMatch
from database.quality_gates import check_unique_nonnull_match_ids, validate_match_points


def ingest(matches_csv: Path, *points_csvs: Path) -> dict:
    matches: list[Match] = []
    players: dict[str, Player] = {}
    parsed_matches, match_parse_errors = parse_matches(matches_csv)
    for match, player_a, player_b in parsed_matches:
        matches.append(match)
        players[player_a.player_id] = player_a
        players[player_b.player_id] = player_b

    match_level_violations = check_unique_nonnull_match_ids(matches) + match_parse_errors

    match_ids = {m.match_id for m in matches}
    points_by_match: dict[str, list[Point]] = {}
    for points_csv in points_csvs:
        parsed_points, point_parse_errors = parse_points_by_match(points_csv, match_ids)
        overlap = set(parsed_points) & set(points_by_match)
        if overlap:
            match_level_violations.append(
                f"{points_csv}: {len(overlap)} match_id(s) already seen in an earlier points file"
            )
        points_by_match.update(parsed_points)
        match_level_violations += point_parse_errors

    outcome_labels: list[OutcomeLabel] = []
    quarantined: list[QuarantinedMatch] = []
    point_violations: dict[str, list[str]] = {}

    matches_by_id = {m.match_id: m for m in matches}
    for match_id, points in points_by_match.items():
        violations = validate_match_points(points)
        if violations:
            point_violations[match_id] = violations
            quarantined.append(QuarantinedMatch(match_id, "; ".join(violations)))
            continue

        outcome = derive_outcome(matches_by_id[match_id], points)
        if isinstance(outcome, QuarantinedMatch):
            quarantined.append(outcome)
        else:
            outcome_labels.append(outcome)

    return {
        "matches_parsed": len(matches),
        "players_parsed": len(players),
        "matches_with_points": len(points_by_match),
        "points_parsed": sum(len(pts) for pts in points_by_match.values()),
        "match_level_violations": match_level_violations,
        "point_level_violations": point_violations,
        "outcome_labels": outcome_labels,
        "quarantined": quarantined,
    }


def _print_report(result: dict) -> None:
    print(f"Matches parsed:          {result['matches_parsed']}")
    print(f"Players parsed:          {result['players_parsed']}")
    print(f"Matches with points:     {result['matches_with_points']}")
    print(f"Points parsed:           {result['points_parsed']}")
    print(f"Match-level violations:  {len(result['match_level_violations'])}")
    print(f"Outcome labels derived:  {len(result['outcome_labels'])}")
    print(f"Matches quarantined:     {len(result['quarantined'])}")
    if result["quarantined"]:
        print("\nQuarantined matches (first 10):")
        for q in result["quarantined"][:10]:
            print(f"  {q.match_id}: {q.reason}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        raise SystemExit(1)
    result = ingest(Path(sys.argv[1]), *(Path(p) for p in sys.argv[2:]))
    _print_report(result)
