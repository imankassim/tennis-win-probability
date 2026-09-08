"""Match data access for the API.

A small Protocol rather than a direct database dependency, so the app can
run against real ingested data or an in-memory fixture without the route
handlers caring which. No live PostgreSQL connection is wired up yet — see
database/README.md — so InMemoryMatchRepository is the only implementation
today, built either from the demo fixture or from real ingested CSVs.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from database.ingestion.match_charting_project import parse_matches, parse_points_by_match
from database.ingestion.outcomes import derive_outcome
from database.models import Match, OutcomeLabel, Player, Point, QuarantinedMatch


class MatchRepository(Protocol):
    def get_match(self, match_id: str) -> Match | None: ...
    def get_player(self, player_id: str) -> Player | None: ...
    def get_points(self, match_id: str) -> list[Point]: ...
    def get_outcome(self, match_id: str) -> OutcomeLabel | None: ...


class InMemoryMatchRepository:
    def __init__(
        self,
        matches: list[Match],
        players: list[Player],
        points_by_match: dict[str, list[Point]],
    ) -> None:
        self._matches = {m.match_id: m for m in matches}
        self._players = {p.player_id: p for p in players}
        self._points = points_by_match
        self._outcomes: dict[str, OutcomeLabel] = {}
        for match_id, points in points_by_match.items():
            match = self._matches.get(match_id)
            if match is None:
                continue
            outcome = derive_outcome(match, points)
            if not isinstance(outcome, QuarantinedMatch):
                self._outcomes[match_id] = outcome

    def get_match(self, match_id: str) -> Match | None:
        return self._matches.get(match_id)

    def get_player(self, player_id: str) -> Player | None:
        return self._players.get(player_id)

    def get_points(self, match_id: str) -> list[Point]:
        return self._points.get(match_id, [])

    def get_outcome(self, match_id: str) -> OutcomeLabel | None:
        return self._outcomes.get(match_id)


def load_from_csv(matches_csv: Path, points_csv: Path) -> InMemoryMatchRepository:
    """Builds a repository from real, freshly-downloaded Match Charting
    Project CSVs (see database/README.md) — not committed to the repo."""
    parsed_matches, _errors = parse_matches(matches_csv)
    matches = [m for m, _a, _b in parsed_matches]
    players: dict[str, Player] = {}
    for _m, player_a, player_b in parsed_matches:
        players[player_a.player_id] = player_a
        players[player_b.player_id] = player_b

    match_ids = {m.match_id for m in matches}
    points_by_match, _errors = parse_points_by_match(points_csv, match_ids)
    return InMemoryMatchRepository(matches, list(players.values()), points_by_match)
