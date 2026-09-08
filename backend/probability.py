"""Computes a probability and price for a given point in a match.

Uses the score-leader heuristic (EXP2, pricing/baselines/) as the
estimator — the Markov chain (Journey 9) and ML model (Journey 11) don't
exist yet. Swapping the estimator later should not require changing this
module's return shape, which already matches the API response contract in
docs/architecture/logical-architecture.md.

The margin applied here is a placeholder flat rate, not the real trading
rules layer (Journey 13) — no suspension, staleness or price-bound checks
are enforced yet. That's why fallback_used and suspended are always False.
"""

from __future__ import annotations

from pricing.baselines.heuristics import score_leader_probability

MODEL_VERSION = "score_leader_heuristic_v0"
_PLACEHOLDER_MARGIN = 0.05


def price_from_probability(probability: float, margin: float = _PLACEHOLDER_MARGIN) -> float:
    return round(1 / (probability * (1 + margin)), 2)


def compute_quote(
    sets_won_a: int,
    sets_won_b: int,
    games_won_a: int,
    games_won_b: int,
) -> tuple[float, float, float]:
    """Returns (probability_player_a, price_player_a, price_player_b)."""
    probability_a = score_leader_probability(
        sets_a=sets_won_a, sets_b=sets_won_b, games_a=games_won_a, games_b=games_won_b
    )
    return (
        probability_a,
        price_from_probability(probability_a),
        price_from_probability(1 - probability_a),
    )
