"""Parser for Jeff Sackmann's Match Charting Project source format.

Source: https://github.com/JeffSackmann/tennis_MatchChartingProject
Licence: CC BY-NC-SA 4.0 (see docs/data_sheets/data_provenance.md).

This module only *reads and transforms* the source CSVs into our domain
records (database/models.py) - it never writes the raw files themselves
into the repository (see the data provenance "no redistribution" rule) and
never touches a database connection. Loading validated records into
PostgreSQL is a separate, later step (see run.py).
"""

from __future__ import annotations

import csv
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from database.models import Match, Player, Point

SOURCE_NAME = "match_charting_project"


def slugify_player_id(name: str) -> str:
    """"Carlos Alcaraz" -> "carlos_alcaraz". Deterministic, matches the
    source's own match_id convention closely enough to stay traceable."""
    slug = name.strip().lower().replace(" ", "_")
    slug = re.sub(r"[^a-z0-9_]", "", slug)
    return slug


def parse_matches(
    csv_path: Path,
) -> tuple[list[tuple[Match, Player, Player]], list[str]]:
    """Parses every row in a charting-*-matches.csv file into
    (match, player_a, player_b) triples. player_a is always "Player 1" -
    the player who served first, per the source's own convention.

    A malformed row (e.g. an unescaped comma in the source shifting every
    later column) is skipped and reported rather than raised - one bad row
    quarantining only itself, not the whole file, per the data
    architecture's quarantine-on-failure rule.
    """
    results: list[tuple[Match, Player, Player]] = []
    errors: list[str] = []
    with csv_path.open(encoding="utf-8") as f:
        for i, row in enumerate(csv.DictReader(f), start=2):  # header is line 1
            match_id = row.get("match_id")
            if not match_id:
                continue
            try:
                player_a = Player(
                    player_id=slugify_player_id(row["Player 1"]),
                    name=row["Player 1"],
                    hand=row.get("Pl 1 hand") or None,
                )
                player_b = Player(
                    player_id=slugify_player_id(row["Player 2"]),
                    name=row["Player 2"],
                    hand=row.get("Pl 2 hand") or None,
                )
                match = Match(
                    match_id=match_id,
                    tournament=row["Tournament"],
                    round=row["Round"],
                    surface=row["Surface"] or "unknown",
                    best_of=int(row["Best of"]),
                    match_date=datetime.strptime(row["Date"], "%Y%m%d").date(),
                    player_a_id=player_a.player_id,
                    player_b_id=player_b.player_id,
                    source=SOURCE_NAME,
                )
            except (ValueError, KeyError) as exc:
                errors.append(f"line {i} ({match_id}): {exc}")
                continue
            results.append((match, player_a, player_b))
    return results, errors


def _side(value: str) -> str:
    return "player_a" if value == "1" else "player_b"


def parse_points_by_match(
    csv_path: Path, match_ids: set[str]
) -> tuple[dict[str, list[Point]], list[str]]:
    """Reads a charting-*-points-*.csv file and returns points grouped by
    match_id, restricted to `match_ids` (matches we have metadata for).

    Point.game_no comes from the source's "Gm#" column, which increments
    exactly at game boundaries - see database/ingestion/outcomes.py for why
    that matters for deriving who won each game without parsing score
    notation.

    As in parse_matches, a malformed row is skipped and reported rather
    than raised.
    """
    points_by_match: dict[str, list[Point]] = defaultdict(list)
    errors: list[str] = []
    with csv_path.open(encoding="utf-8") as f:
        for i, row in enumerate(csv.DictReader(f), start=2):
            match_id = row.get("match_id")
            if match_id not in match_ids:
                continue
            try:
                game_no_raw = row["Gm#"].split(" ")[0]  # "14 (2)" -> "14"
                point = Point(
                    match_id=match_id,
                    point_no=int(row["Pt"]),
                    set_no=int(row["Set1"]) + int(row["Set2"]) + 1,
                    game_no=int(game_no_raw),
                    server=_side(row["Svr"]),
                    point_winner=_side(row["PtWinner"]),
                    sets_won_a=int(row["Set1"]),
                    sets_won_b=int(row["Set2"]),
                    games_won_a=int(row["Gm1"]),
                    games_won_b=int(row["Gm2"]),
                    point_score=row["Pts"],
                )
            except (ValueError, KeyError) as exc:
                errors.append(f"line {i} ({match_id}): {exc}")
                continue
            points_by_match[match_id].append(point)
    for points in points_by_match.values():
        points.sort(key=lambda p: p.point_no)
    return points_by_match, errors
