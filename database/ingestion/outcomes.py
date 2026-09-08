"""Derive an outcome label from a match's points — without parsing score
notation.

Full within-game score parsing (15/30/40/Ad, tiebreak points) is the
match-state parser's job (Journey 6). This module deliberately avoids it
and relies on a simpler, fully reliable signal instead: the source's `Gm#`
column increments exactly at game boundaries, so the *last recorded point
for a given Gm#* is, by definition, the point that won that game —
whatever the internal score notation says. Combined with the sets/games
counts already in the data (state entering that final game), that is
enough to confirm whether a match's final logged point also completed the
match, without reconstructing the full score.

If it doesn't — most commonly because the chart stops mid-match — the
match is quarantined rather than given a guessed outcome, per the data
architecture's quarantine-on-failure rule.
"""

from __future__ import annotations

from database.models import Match, OutcomeLabel, Point, QuarantinedMatch


def _other(side: str) -> str:
    return "player_a" if side == "player_b" else "player_b"


def derive_outcome(match: Match, points: list[Point]) -> OutcomeLabel | QuarantinedMatch:
    if not points:
        return QuarantinedMatch(match.match_id, "no points recorded")

    final_game_no = points[-1].game_no
    final_game_points = [p for p in points if p.game_no == final_game_no]
    first_of_final_game = final_game_points[0]
    game_winner = final_game_points[-1].point_winner
    game_loser = _other(game_winner)

    pre_game = {
        "player_a": first_of_final_game.games_won_a,
        "player_b": first_of_final_game.games_won_b,
    }
    is_tiebreak_game = pre_game["player_a"] == 6 and pre_game["player_b"] == 6

    new_games_winner = pre_game[game_winner] + 1
    new_games_loser = pre_game[game_loser]

    set_completed = is_tiebreak_game or (
        new_games_winner >= 6 and new_games_winner - new_games_loser >= 2
    )
    if not set_completed:
        return QuarantinedMatch(
            match.match_id,
            "final recorded point does not complete a set - chart may be partial",
        )

    pre_set = {
        "player_a": first_of_final_game.sets_won_a,
        "player_b": first_of_final_game.sets_won_b,
    }
    new_sets_winner = pre_set[game_winner] + 1
    new_sets_loser = pre_set[game_loser]

    sets_needed = match.best_of // 2 + 1
    if new_sets_winner < sets_needed:
        return QuarantinedMatch(
            match.match_id,
            "final recorded point completes a set but not the match - chart may be partial",
        )

    return OutcomeLabel(
        match_id=match.match_id,
        actual_winner=game_winner,
        final_score=f"{new_sets_winner}-{new_sets_loser}",
    )
