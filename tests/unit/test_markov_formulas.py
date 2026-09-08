import pytest

from pricing.markov.formulas import (
    prob_win_game,
    prob_win_match,
    prob_win_set,
    prob_win_tiebreak,
)


class TestProbWinGame:
    def test_certain_server_always_wins(self):
        assert prob_win_game(1.0) == 1.0

    def test_server_who_never_wins_a_point_never_wins_the_game(self):
        assert prob_win_game(0.0) == 0.0

    def test_even_point_probability_gives_an_even_game(self):
        assert prob_win_game(0.5) == pytest.approx(0.5)

    def test_deuce_matches_the_known_closed_form(self):
        p = 0.6
        expected = (p * p) / (p * p + (1 - p) * (1 - p))
        assert prob_win_game(p, 3, 3) == pytest.approx(expected)

    def test_service_game_amplifies_a_point_advantage(self):
        # A server who wins points above 50% wins games at an even higher
        # rate — the well-known amplification effect of game scoring.
        assert prob_win_game(0.6) > 0.6

    def test_a_realistic_point_win_rate_gives_a_plausible_hold_rate(self):
        # p=0.65 is a realistic tour-level serve rate; hold rate should
        # land roughly in the 0.80-0.88 range documented in the literature.
        assert 0.80 < prob_win_game(0.65) < 0.88

    def test_already_won_game_returns_one(self):
        assert prob_win_game(0.5, 4, 0) == 1.0

    def test_already_lost_game_returns_zero(self):
        assert prob_win_game(0.5, 0, 4) == 0.0


class TestProbWinTiebreak:
    def test_even_players_split_a_tiebreak_evenly(self):
        assert prob_win_tiebreak(0.5, 0.5) == pytest.approx(0.5)

    def test_better_server_wins_more_tiebreaks(self):
        assert prob_win_tiebreak(0.7, 0.5) > prob_win_tiebreak(0.5, 0.5)

    def test_already_won_tiebreak_returns_one(self):
        assert prob_win_tiebreak(0.6, 0.6, a=7, b=2) == 1.0

    def test_already_lost_tiebreak_returns_zero(self):
        assert prob_win_tiebreak(0.6, 0.6, a=2, b=7) == 0.0

    def test_symmetric_under_swapping_players_and_first_server(self):
        p_a_wins = prob_win_tiebreak(0.65, 0.55, a_serves_point_1=True)
        p_b_wins = prob_win_tiebreak(0.55, 0.65, a_serves_point_1=False)
        assert p_a_wins == pytest.approx(1 - p_b_wins)


class TestProbWinSet:
    def test_even_players_split_a_set_evenly(self):
        assert prob_win_set(0.5, 0.5) == pytest.approx(0.5)

    def test_already_won_set_returns_one(self):
        assert prob_win_set(0.6, 0.6, games_a=6, games_b=2) == 1.0

    def test_six_all_goes_to_a_tiebreak(self):
        direct = prob_win_set(0.6, 0.55, games_a=6, games_b=6, a_serves_next=True)
        expected = prob_win_tiebreak(0.6, 0.55, a_serves_point_1=True)
        assert direct == expected

    def test_better_server_wins_more_sets(self):
        assert prob_win_set(0.65, 0.55) > prob_win_set(0.55, 0.65)

    def test_who_serves_first_does_not_matter_from_a_fresh_set(self):
        # Verified independently by Monte Carlo simulation, not just this
        # recursion: from 0-0 games, alternating service means the set-win
        # probability is identical whichever player serves game 1 — a real
        # property, not a bug. It does start to matter mid-set (see
        # test_better_server_wins_more_sets-style state-dependent cases).
        assert prob_win_set(0.6, 0.55, 0, 0, True) == prob_win_set(0.6, 0.55, 0, 0, False)

    def test_who_serves_first_does_matter_mid_set(self):
        assert prob_win_set(0.6, 0.55, 3, 2, True) != prob_win_set(0.6, 0.55, 3, 2, False)

    def test_an_advantage_set_deep_past_six_all_does_not_recurse_forever(self):
        # Real historical data (pre-2022-era deciding sets played without
        # a tiebreak) can reach scores like 10-9 or deeper. This must
        # terminate (via truncation past a combined-games cap), not raise
        # a RecursionError — caught from real ingested data.
        result = prob_win_set(0.55, 0.5, games_a=10, games_b=9, a_serves_next=True)
        assert 0.0 <= result <= 1.0

    def test_advantage_set_still_resolves_a_clear_lead_correctly(self):
        # Below the truncation cap, a 2-game lead past 6-6 must still be
        # a clean win, not a truncated coin flip.
        assert prob_win_set(0.6, 0.5, games_a=10, games_b=8) == 1.0
        assert prob_win_set(0.6, 0.5, games_a=8, games_b=10) == 0.0


class TestProbWinMatch:
    def test_even_players_split_a_best_of_three_evenly(self):
        assert prob_win_match(0.5, 0.5, best_of=3) == pytest.approx(0.5)

    def test_even_players_split_a_best_of_five_evenly(self):
        assert prob_win_match(0.5, 0.5, best_of=5) == pytest.approx(0.5)

    def test_already_won_enough_sets_returns_one(self):
        assert prob_win_match(0.5, 0.5, best_of=3, sets_a=2) == 1.0

    def test_already_lost_returns_zero(self):
        assert prob_win_match(0.5, 0.5, best_of=5, sets_b=3) == 0.0

    def test_a_stronger_server_is_a_bigger_favourite_in_the_match_than_in_one_game(self):
        # Repeated independent-ish advantages compound over a whole match.
        game_edge = prob_win_game(0.55) - 0.5
        match_edge = prob_win_match(0.55, 0.45) - 0.5
        assert match_edge > game_edge

    def test_symmetric_under_swapping_players(self):
        # a_serves_next must flip too: "A serves" in the original scenario
        # means "B serves" once the players' roles are swapped.
        p_a_wins = prob_win_match(
            0.62, 0.58, best_of=3, sets_a=1, games_a=3, games_b=2, a_serves_next=True
        )
        p_b_wins = prob_win_match(
            0.58, 0.62, best_of=3, sets_b=1, games_b=3, games_a=2, a_serves_next=False
        )
        assert p_a_wins == pytest.approx(1 - p_b_wins)

    def test_reflects_a_two_sets_to_love_deficit_but_leaves_room_for_recovery(self):
        # Down two sets to love in a best-of-five with an otherwise even
        # matchup: heavily unfavoured, but not zero (recovery scenario).
        p = prob_win_match(0.5, 0.5, best_of=5, sets_a=0, sets_b=2)
        assert 0.0 < p < 0.3
