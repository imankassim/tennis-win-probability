"""Computes a probability and price for a given point in a match.

Uses the Markov engine (pricing/markov/, Journey 9) as the estimator —
replacing the score-leader heuristic (EXP2) that served as a placeholder
from Journey 5 until a real analytic baseline existed. The ML model
(Journey 11) doesn't exist yet. Swapping the estimator again later should
not require changing this module's return shape, which already matches
the API response contract in docs/architecture/logical-architecture.md.

The margin applied here is a placeholder flat rate, not the real trading
rules layer (Journey 13) — no suspension, staleness or price-bound checks
are enforced yet. That's why fallback_used and suspended are always False
in main.py's response.
"""

from __future__ import annotations

from pricing.markov.engine import markov_probability

MODEL_VERSION = "markov_v1"
_PLACEHOLDER_MARGIN = 0.05


def price_from_probability(probability: float, margin: float = _PLACEHOLDER_MARGIN) -> float:
    return round(1 / (probability * (1 + margin)), 2)


def compute_quote(
    p_a_serve_rate: float,
    p_b_serve_rate: float,
    best_of: int,
    sets_won_a: int,
    sets_won_b: int,
    games_won_a: int,
    games_won_b: int,
    server: str,
    points_a: int = 0,
    points_b: int = 0,
) -> tuple[float, float, float]:
    """Returns (probability_player_a, price_player_a, price_player_b)."""
    probability_a = markov_probability(
        p_a_serve_rate,
        p_b_serve_rate,
        best_of,
        sets_won_a,
        sets_won_b,
        games_won_a,
        games_won_b,
        server,
        points_a,
        points_b,
    )
    return (
        probability_a,
        price_from_probability(probability_a),
        price_from_probability(1 - probability_a),
    )
