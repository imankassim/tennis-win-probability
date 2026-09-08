"""Feature dataset construction for the ML win-probability model
(Journey 11): EXP20-24.

Two feature groups, per the planned experiment catalogue:
- **State features**: score state only (sets, games, points, server,
  best_of) — always included, since even the weakest ML configuration
  (EXP20) needs a score state to condition on.
- **Context features**: recent form, surface record, head-to-head, and
  Elo rating (EXP21+), plus within-match momentum (EXP24).

Context features are computed once per MATCH, not once per point:
`compute_match_context_features` does a single pass through the whole
archive in date order (the same running-totals pattern as
backend/player_rating.py and pricing/markov/serve_rate.py's bulk
functions) rather than calling backend/context_features.py's per-match
functions once per match, which would each rescan the archive — fine for
one live lookup, O(matches²) for building a training set. Momentum is a
true within-match feature (this match's own recent points), computed
directly while building the point-level rows, no archive scan needed.

Same no-look-ahead discipline as everywhere else in this codebase: a
match's context features reflect only earlier matches; a point's state
features reflect only earlier points in the same match.
"""

from __future__ import annotations

from collections import defaultdict, deque

import pandas as pd

from backend.player_rating import compute_rating_history, rating_as_of
from database.models import Match, OutcomeLabel, Point

FORM_LOOKBACK = 10
MOMENTUM_LOOKBACK = 10
DEFAULT_FORM = 0.5  # neutral — "no prior data" is not "poor form"


def compute_match_context_features(
    matches: list[Match], outcomes: dict[str, OutcomeLabel]
) -> dict[str, dict[str, float]]:
    """One pass through every match with a confirmed outcome, in date
    order: recent form, surface win rate, head-to-head and Elo rating for
    both players, as of each match's own date."""
    resolved = [m for m in matches if m.match_id in outcomes]
    ordered = sorted(resolved, key=lambda m: m.match_date)

    elo_history = compute_rating_history(matches, outcomes)

    form_history: dict[str, deque] = defaultdict(lambda: deque(maxlen=FORM_LOOKBACK))
    surface_wins: dict[tuple[str, str], int] = defaultdict(int)
    surface_losses: dict[tuple[str, str], int] = defaultdict(int)
    h2h_wins: dict[frozenset, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    result: dict[str, dict[str, float]] = {}

    for match in ordered:
        a, b = match.player_a_id, match.player_b_id
        surface = match.surface.lower()

        form_a_hist = form_history[a]
        form_b_hist = form_history[b]
        form_a = sum(form_a_hist) / len(form_a_hist) if form_a_hist else DEFAULT_FORM
        form_b = sum(form_b_hist) / len(form_b_hist) if form_b_hist else DEFAULT_FORM

        sw_a, sl_a = surface_wins[(a, surface)], surface_losses[(a, surface)]
        sw_b, sl_b = surface_wins[(b, surface)], surface_losses[(b, surface)]
        surface_rate_a = sw_a / (sw_a + sl_a) if (sw_a + sl_a) else DEFAULT_FORM
        surface_rate_b = sw_b / (sw_b + sl_b) if (sw_b + sl_b) else DEFAULT_FORM

        pair = frozenset({a, b})
        h2h_a = h2h_wins[pair][a]
        h2h_b = h2h_wins[pair][b]
        h2h_total = h2h_a + h2h_b
        h2h_rate_a = h2h_a / h2h_total if h2h_total else DEFAULT_FORM

        elo_a = rating_as_of(a, elo_history, match.match_date)
        elo_b = rating_as_of(b, elo_history, match.match_date)

        result[match.match_id] = {
            "form_a": form_a,
            "form_b": form_b,
            "surface_rate_a": surface_rate_a,
            "surface_rate_b": surface_rate_b,
            "h2h_rate_a": h2h_rate_a,
            "elo_a": elo_a,
            "elo_b": elo_b,
        }

        # Now fold this match's own result into the running state.
        outcome = outcomes[match.match_id]
        a_won = outcome.actual_winner == "player_a"
        form_a_hist.append(a_won)
        form_b_hist.append(not a_won)
        if a_won:
            surface_wins[(a, surface)] += 1
            surface_losses[(b, surface)] += 1
        else:
            surface_wins[(b, surface)] += 1
            surface_losses[(a, surface)] += 1
        h2h_wins[pair][a if a_won else b] += 1

    return result


def _momentum(recent_winners: list[str], side: str) -> float:
    """Fraction of the last MOMENTUM_LOOKBACK points won by `side` within
    this match. DEFAULT_FORM (neutral) if there's no history yet — the
    very start of a match carries no momentum signal either way."""
    if not recent_winners:
        return DEFAULT_FORM
    window = recent_winners[-MOMENTUM_LOOKBACK:]
    return sum(1 for w in window if w == side) / len(window)


def build_point_features(
    matches: list[Match],
    points_by_match: dict[str, list[Point]],
    outcomes: dict[str, OutcomeLabel],
    match_context: dict[str, dict[str, float]],
) -> pd.DataFrame:
    """One row per point, from every match with a confirmed outcome.
    Always includes state + momentum features; context features are only
    meaningful once `match_context` (from compute_match_context_features)
    is supplied — callers select feature subsets afterward (EXP20 vs
    EXP21 etc.), this just builds the full superset once."""
    rows = []
    matches_by_id = {m.match_id: m for m in matches}

    for match_id, points in points_by_match.items():
        outcome = outcomes.get(match_id)
        if outcome is None:
            continue
        match = matches_by_id[match_id]
        label = 1 if outcome.actual_winner == "player_a" else 0
        context = match_context.get(match_id, {})
        recent_winners: list[str] = []

        for point in points:
            rows.append(
                {
                    "match_id": match_id,
                    "point_no": point.point_no,
                    "match_date": match.match_date,
                    "label": label,
                    # State features (always present).
                    "best_of": match.best_of,
                    "sets_a": point.sets_won_a,
                    "sets_b": point.sets_won_b,
                    "games_a": point.games_won_a,
                    "games_b": point.games_won_b,
                    "server_is_a": 1 if point.server == "player_a" else 0,
                    # Momentum (within-match, always present).
                    "momentum_a": _momentum(recent_winners, "player_a"),
                    # Context features (present once match_context is populated).
                    "form_a": context.get("form_a"),
                    "form_b": context.get("form_b"),
                    "surface_rate_a": context.get("surface_rate_a"),
                    "surface_rate_b": context.get("surface_rate_b"),
                    "h2h_rate_a": context.get("h2h_rate_a"),
                    "elo_a": context.get("elo_a"),
                    "elo_b": context.get("elo_b"),
                }
            )
            recent_winners.append(point.point_winner)

    return pd.DataFrame(rows)


STATE_FEATURES = ["best_of", "sets_a", "sets_b", "games_a", "games_b", "server_is_a"]
CONTEXT_FEATURES = [
    "form_a",
    "form_b",
    "surface_rate_a",
    "surface_rate_b",
    "h2h_rate_a",
    "elo_a",
    "elo_b",
]
MOMENTUM_FEATURES = ["momentum_a"]
