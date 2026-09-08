"""The player context service (logical architecture component B2):
deterministic ranking, recent form, surface and head-to-head extraction.

Recent form, surface record and head-to-head are computed directly from
our own ingested match archive (database/models.py Match + OutcomeLabel) —
no external source needed, since they're just aggregates over matches we
already have. Player strength ("ranking") is NOT computed here: no
external ranking feed was ever sourced (Player.current_rank/rank_points
stay unpopulated — see docs/data_sheets/data_provenance.md), so
backend/player_rating.py computes a self-sufficient Elo rating from this
same archive instead — a separate module since it needs its own
sequential, whole-archive pass (a running rating per player) rather than
a per-match aggregate like the functions here.

Every function here takes `as_of_date` and strictly excludes matches on or
after it — the "no look-ahead" training control (ADR 9's context, and
docs/architecture/offline-training-architecture.md): a context feature for
a match must never see that match's own result, or any later one. This is
the same reason match_date uses a strict `<`, not `<=` — two matches on the
same recorded date have no reliable intra-day ordering in this data, so
being strict is the safe default. This module is meant to be imported
identically by the live API and by offline feature generation (Journey 11)
once it exists, per the "same code in training and serving" control.
"""

from __future__ import annotations

from datetime import date

from database.models import Match, OutcomeLabel


def _player_matches_before(
    player_id: str,
    matches: list[Match],
    as_of_date: date,
) -> list[Match]:
    return [
        m
        for m in matches
        if m.match_date < as_of_date and player_id in (m.player_a_id, m.player_b_id)
    ]


def _won(match: Match, player_id: str, outcomes: dict[str, OutcomeLabel]) -> bool | None:
    outcome = outcomes.get(match.match_id)
    if outcome is None:
        return None
    winner_id = match.player_a_id if outcome.actual_winner == "player_a" else match.player_b_id
    return winner_id == player_id


def recent_form(
    player_id: str,
    matches: list[Match],
    outcomes: dict[str, OutcomeLabel],
    as_of_date: date,
    lookback: int = 10,
) -> float | None:
    """Win rate over the player's last `lookback` completed matches before
    as_of_date. None if there are no prior completed matches (an unknown
    quantity, not zero — do not silently treat a debutant as "in poor
    form")."""
    prior = sorted(
        _player_matches_before(player_id, matches, as_of_date), key=lambda m: m.match_date
    )
    results = [_won(m, player_id, outcomes) for m in prior]
    results = [r for r in results if r is not None]
    if not results:
        return None
    recent = results[-lookback:]
    return sum(recent) / len(recent)


def surface_record(
    player_id: str,
    surface: str,
    matches: list[Match],
    outcomes: dict[str, OutcomeLabel],
    as_of_date: date,
) -> tuple[int, int]:
    """(wins, losses) for the player on `surface` before as_of_date.
    Matches with no confirmed outcome are excluded from both counts."""
    prior = _player_matches_before(player_id, matches, as_of_date)
    wins = losses = 0
    for m in prior:
        if m.surface.lower() != surface.lower():
            continue
        won = _won(m, player_id, outcomes)
        if won is True:
            wins += 1
        elif won is False:
            losses += 1
    return wins, losses


def head_to_head(
    player_a_id: str,
    player_b_id: str,
    matches: list[Match],
    outcomes: dict[str, OutcomeLabel],
    as_of_date: date,
) -> tuple[int, int]:
    """(wins for player_a_id, wins for player_b_id) in matches between
    exactly these two players before as_of_date."""
    prior = [
        m
        for m in matches
        if m.match_date < as_of_date
        and {m.player_a_id, m.player_b_id} == {player_a_id, player_b_id}
    ]
    wins_a = wins_b = 0
    for m in prior:
        if _won(m, player_a_id, outcomes) is True:
            wins_a += 1
        elif _won(m, player_b_id, outcomes) is True:
            wins_b += 1
    return wins_a, wins_b
