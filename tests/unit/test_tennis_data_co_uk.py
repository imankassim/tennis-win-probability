from datetime import date

from database.ingestion.tennis_data_co_uk import MarketOddsRow, match_market_odds_to_archive
from database.models import Match


def _match(match_id, d, p1, p2):
    return Match(
        match_id=match_id,
        tournament="t",
        round="F",
        surface="hard",
        best_of=3,
        match_date=d,
        player_a_id=p1,
        player_b_id=p2,
        source="test",
    )


def test_matches_by_surname_and_close_date():
    matches = [_match("m1", date(2026, 1, 5), "p_a", "p_b")]
    players = {"p_a": "Frances Tiafoe", "p_b": "Alex De Minaur"}
    market_rows = [
        MarketOddsRow(
            match_date=date(2026, 1, 6),  # 1 day off — within tolerance
            winner_name="Tiafoe F.",
            loser_name="De Minaur A.",
            avg_odds_winner=1.5,
            avg_odds_loser=2.6,
        )
    ]
    result = match_market_odds_to_archive(market_rows, matches, players)
    assert "m1" in result
    odds_a, odds_b = result["m1"]
    assert odds_a == 1.5  # player_a (Tiafoe) is the recorded winner
    assert odds_b == 2.6


def test_orients_odds_to_player_a_player_b_regardless_of_who_won():
    matches = [_match("m1", date(2026, 1, 5), "p_a", "p_b")]
    players = {"p_a": "Frances Tiafoe", "p_b": "Alex De Minaur"}
    # This time De Minaur (player_b) is recorded as the winner.
    market_rows = [
        MarketOddsRow(
            match_date=date(2026, 1, 5),
            winner_name="De Minaur A.",
            loser_name="Tiafoe F.",
            avg_odds_winner=1.8,
            avg_odds_loser=2.0,
        )
    ]
    result = match_market_odds_to_archive(market_rows, matches, players)
    odds_a, odds_b = result["m1"]
    assert odds_a == 2.0  # player_a (Tiafoe) was the loser here
    assert odds_b == 1.8


def test_does_not_match_when_date_is_too_far_off():
    matches = [_match("m1", date(2026, 1, 1), "p_a", "p_b")]
    players = {"p_a": "Frances Tiafoe", "p_b": "Alex De Minaur"}
    market_rows = [
        MarketOddsRow(
            match_date=date(2026, 2, 1),  # far outside tolerance
            winner_name="Tiafoe F.",
            loser_name="De Minaur A.",
            avg_odds_winner=1.5,
            avg_odds_loser=2.6,
        )
    ]
    result = match_market_odds_to_archive(market_rows, matches, players)
    assert result == {}


def test_does_not_match_unrelated_players():
    matches = [_match("m1", date(2026, 1, 5), "p_a", "p_b")]
    players = {"p_a": "Frances Tiafoe", "p_b": "Alex De Minaur"}
    market_rows = [
        MarketOddsRow(
            match_date=date(2026, 1, 5),
            winner_name="Djokovic N.",
            loser_name="Alcaraz C.",
            avg_odds_winner=1.5,
            avg_odds_loser=2.6,
        )
    ]
    result = match_market_odds_to_archive(market_rows, matches, players)
    assert result == {}
