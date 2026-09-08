"""Parser for tennis-data.co.uk historical match odds.

Source: http://tennis-data.co.uk/alldata.php
Used strictly as an evaluation benchmark (decision 8, decision on public
data sources) — never as a serving-time feature, never treated as ground
truth of the "true" probability. See
docs/data_sheets/data_provenance.md and
trading_rules/value_detection.py's module docstring for the bounded,
research-only framing this feeds into.

This module only parses the source file and matches its rows to our own
archive by player name (tennis-data.co.uk has no shared match_id with the
Match Charting Project) — it does not compute any probability or flag
itself.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from database.models import Match

# How close a tennis-data.co.uk row's date must be to one of our match's
# recorded date to be considered the same match — the two sources don't
# always record identical calendar dates for a single tournament's
# matches (e.g. tournament start date vs. the specific match's date).
DATE_TOLERANCE_DAYS = 3


@dataclass(frozen=True)
class MarketOddsRow:
    match_date: date
    winner_name: str
    loser_name: str
    avg_odds_winner: float
    avg_odds_loser: float


def _surname(name: str) -> str:
    """"Tiafoe F." -> "tiafoe"; "Frances Tiafoe" -> "tiafoe". Handles both
    the source's "Surname Initial." convention and our own "First Last"
    player names by taking whichever token isn't a bare initial."""
    tokens = [t.strip(".") for t in name.strip().split()]
    tokens = [t for t in tokens if len(t) > 1]  # drop single-letter initials
    if not tokens:
        return name.strip().lower()
    return tokens[0].lower() if len(tokens) == 1 else tokens[-1].lower()


def parse_market_odds(xlsx_path: Path) -> list[MarketOddsRow]:
    """Reads one of tennis-data.co.uk's yearly ATP/WTA files. Rows with a
    missing date or odds are skipped rather than raised, consistent with
    the ingestion pipeline's "skip and report" handling of malformed
    source rows elsewhere in this codebase."""
    df = pd.read_excel(xlsx_path)
    rows = []
    for _, row in df.iterrows():
        try:
            match_date = pd.to_datetime(row["Date"]).date()
            avg_w = float(row["AvgW"])
            avg_l = float(row["AvgL"])
        except (KeyError, ValueError, TypeError):
            continue
        if pd.isna(avg_w) or pd.isna(avg_l):
            continue
        rows.append(
            MarketOddsRow(
                match_date=match_date,
                winner_name=str(row["Winner"]),
                loser_name=str(row["Loser"]),
                avg_odds_winner=avg_w,
                avg_odds_loser=avg_l,
            )
        )
    return rows


def match_market_odds_to_archive(
    market_rows: list[MarketOddsRow], matches: list[Match], players_by_id: dict[str, str]
) -> dict[str, tuple[float, float]]:
    """Matches market odds rows to our own archive by (surname pair, date
    proximity). Returns {match_id: (odds_a, odds_b)} — odds for player_a
    and player_b as recorded in *our* Match, not the source's
    winner/loser framing (the outcome isn't known to a real bettor before
    the match, so orienting by our fixed player_a/player_b avoids
    accidentally encoding the result into which side "odds_a" is).

    Deliberately not exhaustive — matches only what it can confirm via
    both players' surnames and a close date; unmatched rows are simply
    absent from the result, not guessed at.
    """
    surname_pairs: dict[frozenset, list[Match]] = {}
    for m in matches:
        name_a = players_by_id.get(m.player_a_id, "")
        name_b = players_by_id.get(m.player_b_id, "")
        key = frozenset({_surname(name_a), _surname(name_b)})
        surname_pairs.setdefault(key, []).append(m)

    result: dict[str, tuple[float, float]] = {}
    for row in market_rows:
        key = frozenset({_surname(row.winner_name), _surname(row.loser_name)})
        candidates = surname_pairs.get(key)
        if not candidates:
            continue
        for m in candidates:
            if abs((m.match_date - row.match_date).days) > DATE_TOLERANCE_DAYS:
                continue
            name_a = players_by_id.get(m.player_a_id, "")
            winner_is_a = _surname(row.winner_name) == _surname(name_a)
            odds_a = row.avg_odds_winner if winner_is_a else row.avg_odds_loser
            odds_b = row.avg_odds_loser if winner_is_a else row.avg_odds_winner
            result[m.match_id] = (odds_a, odds_b)
            break

    return result
