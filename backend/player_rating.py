"""Player strength rating (finishing Journey 10's remaining scope:
"ranking").

No external rankings feed has been found - the originally-named sources
are gone (docs/data_sheets/data_provenance.md) and official ATP/WTA points
aren't published anywhere with a confirmed non-commercial licence. Rather
than another lengthy data-source hunt, this computes a standard Elo rating
directly from our own ingested match archive - self-sufficient, and
arguably more directly relevant to in-play prediction than official
ranking points anyway (ATP points are shaped by tournament-category
weighting and 52-week accounting, not pure recent head-to-head strength).

Same no-look-ahead discipline as context_features.py and serve_rate.py:
a rating "as of" a date only reflects matches strictly before it.
"""

from __future__ import annotations

import bisect
from collections import defaultdict
from datetime import date

from database.models import Match, OutcomeLabel

DEFAULT_RATING = 1500.0
# Standard chess-Elo K-factor, untuned against this data - a genuine
# follow-up experiment (sweeping K) once there's a held-out set to tune
# against, same as EXP13's shrinkage strength.
K_FACTOR = 32.0


def _expected_score(rating_a: float, rating_b: float) -> float:
    return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / 400.0))


def compute_rating_history(
    matches: list[Match], outcomes: dict[str, OutcomeLabel]
) -> dict[str, list[tuple[date, float]]]:
    """One pass through every match with a confirmed outcome, in date
    order, updating both players' Elo ratings. Returns each player's
    rating immediately after each of their matches, sorted by date -
    the history `rating_as_of` looks up into."""
    ratings: dict[str, float] = defaultdict(lambda: DEFAULT_RATING)
    history: dict[str, list[tuple[date, float]]] = defaultdict(list)

    resolved = [m for m in matches if m.match_id in outcomes]
    for match in sorted(resolved, key=lambda m: m.match_date):
        outcome = outcomes[match.match_id]
        rating_a = ratings[match.player_a_id]
        rating_b = ratings[match.player_b_id]
        expected_a = _expected_score(rating_a, rating_b)
        actual_a = 1.0 if outcome.actual_winner == "player_a" else 0.0

        new_rating_a = rating_a + K_FACTOR * (actual_a - expected_a)
        new_rating_b = rating_b + K_FACTOR * ((1 - actual_a) - (1 - expected_a))
        ratings[match.player_a_id] = new_rating_a
        ratings[match.player_b_id] = new_rating_b
        history[match.player_a_id].append((match.match_date, new_rating_a))
        history[match.player_b_id].append((match.match_date, new_rating_b))

    return dict(history)


def rating_as_of(
    player_id: str,
    history: dict[str, list[tuple[date, float]]],
    as_of_date: date,
) -> float:
    """The player's rating from their most recent match strictly before
    as_of_date. DEFAULT_RATING if they have no such match (an untested
    player, not a weak one - a neutral, not a punitive, default)."""
    player_history = history.get(player_id)
    if not player_history:
        return DEFAULT_RATING
    dates = [d for d, _ in player_history]
    index = bisect.bisect_left(dates, as_of_date)
    if index == 0:
        return DEFAULT_RATING
    return player_history[index - 1][1]
