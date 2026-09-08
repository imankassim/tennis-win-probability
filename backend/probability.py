"""Computes a probability for a given point in a match.

Uses the Markov engine (pricing/markov/, Journey 9) as the estimator —
replacing the score-leader heuristic (EXP2) that served as a placeholder
from Journey 5 until a real analytic baseline existed. The ML model
(Journey 11) and the tuned blend (Journey 12) both beat Markov in
evaluation but aren't wired in here yet — see pricing/blend/README.md for
why. Swapping the estimator again later should not require changing this
module's return shape.

Pricing (margin, price bounds, suspension) is trading_rules/rules.py's
job, not this module's — this only returns the raw probability estimate.
"""

from __future__ import annotations

from pricing.markov.engine import markov_probability

MODEL_VERSION = "markov_v1"


def compute_probability(
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
) -> float:
    return markov_probability(
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
