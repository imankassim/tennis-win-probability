"""Domain records for the data foundation (Journey 4).

These mirror the operational entities in
docs/architecture/data-architecture.md. They are plain dataclasses, not ORM
models - the schema they map onto lives in database/schema.sql, and nothing
here assumes a particular database driver.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Player:
    player_id: str
    name: str
    hand: str | None = None


@dataclass(frozen=True)
class Match:
    match_id: str
    tournament: str
    round: str
    surface: str
    best_of: int
    match_date: date
    player_a_id: str
    player_b_id: str
    source: str


@dataclass(frozen=True)
class Point:
    match_id: str
    point_no: int
    set_no: int
    game_no: int
    server: str  # "player_a" | "player_b"
    point_winner: str  # "player_a" | "player_b"
    # Raw score state as recorded by the source, preserved rather than
    # reinterpreted - the data-architecture Point entity explicitly allows
    # this. Turning it into a clean "games: '4-4'"-style interpretation is
    # the match-state parser's job (Journey 6), not ingestion's.
    # All four *_won_* fields are the state entering this point (completed
    # games/sets so far), not including this point's own outcome.
    sets_won_a: int
    sets_won_b: int
    games_won_a: int
    games_won_b: int
    point_score: str


@dataclass(frozen=True)
class OutcomeLabel:
    match_id: str
    actual_winner: str  # "player_a" | "player_b"
    final_score: str  # sets only, e.g. "3-1" - see outcomes.py


@dataclass(frozen=True)
class QuarantinedMatch:
    """A match whose data failed a quality gate or couldn't be confirmed
    complete - excluded from outcome labels rather than guessed at."""

    match_id: str
    reason: str
