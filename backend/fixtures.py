"""A small, synthetic demo match - not real data, used only so the API has
something to serve without requiring a real ingested dataset (see
database/README.md for loading real data instead). Mirrors the same
"clearly labelled, never confused with real data" approach as
frontend/src/lib/mockData.ts.
"""

from __future__ import annotations

from datetime import date

from database.models import Match, Player, Point

DEMO_MATCH_ID = "demo_backend_001"

_PLAYER_A = Player(player_id="demo_player_a", name="Demo Player A")
_PLAYER_B = Player(player_id="demo_player_b", name="Demo Player B")

_MATCH = Match(
    match_id=DEMO_MATCH_ID,
    tournament="Demo Open",
    round="F",
    surface="hard",
    best_of=3,
    match_date=date(2026, 1, 1),
    player_a_id=_PLAYER_A.player_id,
    player_b_id=_PLAYER_B.player_id,
    source="synthetic_demo_fixture",
)


def _other(side: str) -> str:
    return "player_b" if side == "player_a" else "player_a"


def _hold(server: str, opponent_points_won: int = 0) -> tuple[str, list[str]]:
    """The server wins the game; the receiver wins `opponent_points_won` (0-2) points first."""
    receiver = _other(server)
    return server, [receiver] * opponent_points_won + [server] * 4


def _break(server: str, server_points_won: int = 0) -> tuple[str, list[str]]:
    """The receiver wins the game; the server wins `server_points_won` (0-2) points first."""
    receiver = _other(server)
    return server, [server] * server_points_won + [receiver] * 4


def _build_points() -> list[Point]:
    # Set 1: eight holds (4-4), then player_a breaks and holds to close it
    # 6-4. Set 2: three more holds, left in progress at 3-2 to player_a.
    games = [
        _hold("player_a"),
        _hold("player_b"),
        _hold("player_a", 1),
        _hold("player_b", 1),
        _hold("player_a"),
        _hold("player_b", 2),
        _hold("player_a", 1),
        _hold("player_b"),
        _break("player_b", 1),  # player_a breaks: 5-4
        _hold("player_a"),  # player_a closes the set: 6-4
        # set 2, left in progress
        _hold("player_a"),
        _hold("player_b", 1),
        _hold("player_a", 2),
        _hold("player_b"),
        _hold("player_a", 1),
    ]

    points: list[Point] = []
    point_no = 0
    sets_a = sets_b = 0
    games_a = games_b = 0
    set_no = 1
    for game_idx, (server, winners) in enumerate(games):
        game_winner = winners[-1]
        for winner in winners:
            point_no += 1
            points.append(
                Point(
                    match_id=DEMO_MATCH_ID,
                    point_no=point_no,
                    set_no=set_no,
                    game_no=game_idx + 1,
                    server=server,
                    point_winner=winner,
                    sets_won_a=sets_a,
                    sets_won_b=sets_b,
                    games_won_a=games_a,
                    games_won_b=games_b,
                    point_score="n/a",
                )
            )
        if game_winner == "player_a":
            games_a += 1
        else:
            games_b += 1

        winner_games = max(games_a, games_b)
        loser_games = min(games_a, games_b)
        if winner_games >= 6 and winner_games - loser_games >= 2:
            if games_a > games_b:
                sets_a += 1
            else:
                sets_b += 1
            games_a = games_b = 0
            set_no += 1
    return points


def demo_repository_data() -> tuple[list[Match], list[Player], dict[str, list[Point]]]:
    return [_MATCH], [_PLAYER_A, _PLAYER_B], {DEMO_MATCH_ID: _build_points()}
