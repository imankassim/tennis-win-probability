"""Match data access for the API.

A small Protocol rather than a direct database dependency, so the app can
run against real ingested data or an in-memory fixture without the route
handlers caring which. No live PostgreSQL connection is wired up yet - see
database/README.md - so InMemoryMatchRepository is the only implementation
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
    def list_matches(self) -> list[Match]: ...
    def all_points_by_match(self) -> dict[str, list[Point]]: ...
    def all_outcomes(self) -> dict[str, OutcomeLabel]: ...


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

    def list_matches(self) -> list[Match]:
        """Only matches that actually have points loaded - a match with no
        points isn't replayable. `load_from_csv` may parse thousands of
        rows of match metadata against only a bounded sample of points."""
        return [m for match_id, m in self._matches.items() if self._points.get(match_id)]

    def all_points_by_match(self) -> dict[str, list[Point]]:
        """For serve-rate estimation (pricing/markov/serve_rate.py), which
        needs every player's history across the whole archive, not just
        one match's points."""
        return self._points

    def all_outcomes(self) -> dict[str, OutcomeLabel]:
        """For context-feature estimation (pricing/ml/features.py), the
        same bulk-access shape as all_points_by_match - the ML context
        cache needs every match's confirmed outcome, not just one."""
        return self._outcomes


def load_from_csv(matches_csv: Path, *points_csvs: Path) -> InMemoryMatchRepository:
    """Builds a repository from real, freshly-downloaded Match Charting
    Project CSVs (see database/README.md) - not committed to the repo.
    Accepts multiple points files (e.g. one per decade - real match_ids
    never repeat across them), same as database/ingestion/run.py."""
    parsed_matches, _errors = parse_matches(matches_csv)
    matches = [m for m, _a, _b in parsed_matches]
    players: dict[str, Player] = {}
    for _m, player_a, player_b in parsed_matches:
        players[player_a.player_id] = player_a
        players[player_b.player_id] = player_b

    match_ids = {m.match_id for m in matches}
    points_by_match: dict[str, list[Point]] = {}
    for points_csv in points_csvs:
        parsed_points, _errors = parse_points_by_match(points_csv, match_ids)
        points_by_match.update(parsed_points)
    return InMemoryMatchRepository(matches, list(players.values()), points_by_match)
