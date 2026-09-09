"""The bounded, research-only value-detection layer (Journey 15).

Per the logical architecture (step 10): "A bounded value-flag compares
the resulting price with the last known market price, for research
analysis only, without altering the served probability." Per decision 8
and docs/architecture/risk_register.md's "market-odds benchmark
limitations" row: market odds are de-vigged before any comparison and
this is framed strictly as research, not as betting advice or a staking
recommendation - nothing here computes a stake, a bankroll effect, or
anything resembling betting guidance, and the flag never feeds back into
the served probability.

"Bounded" means two things, both enforced here: the reported edge is
capped (an extreme edge almost always means a data problem - a bad match
or a stale price - not a genuine 40-point mispricing), and the flag is a
label, not a number to act on.
"""

from __future__ import annotations

from dataclasses import dataclass

# An edge past this is treated as a data-quality signal, not a genuine
# opportunity - real closing-line mispricings this large are vanishingly
# rare; this size almost always means a bad player match or a stale/wrong
# price got through. Capping, not clipping to zero, keeps the flag
# informative about direction while refusing to imply "beat the market by
# 40 points" is a real, actionable finding.
MAX_REPORTED_EDGE = 0.15
# Below this, don't flag at all - normal estimation noise between two
# independently-built probabilities, not a meaningful disagreement.
FLAG_THRESHOLD = 0.05


@dataclass(frozen=True)
class ValueFlag:
    model_probability: float
    market_probability: float
    edge: float  # capped to +/- MAX_REPORTED_EDGE
    flagged: bool  # |edge| exceeds FLAG_THRESHOLD


def devig_odds(odds_a: float, odds_b: float) -> tuple[float, float]:
    """Removes the bookmaker's overround (multiplicative method): the raw
    implied probabilities from decimal odds sum to more than 1 (the
    margin); dividing each by that sum rescales them to sum to exactly 1,
    the standard de-vig approach docs/architecture/risk_register.md
    references."""
    if odds_a <= 1.0 or odds_b <= 1.0:
        raise ValueError("decimal odds must be greater than 1.0")
    raw_a = 1 / odds_a
    raw_b = 1 / odds_b
    total = raw_a + raw_b
    return raw_a / total, raw_b / total


def compute_value_flag(model_probability: float, odds_a: float, odds_b: float) -> ValueFlag:
    """Compares a model probability for player A against the de-vigged
    market-implied probability for the same side. Never called from the
    live pricing path - this is an offline/research comparison only (see
    the module docstring)."""
    market_probability_a, _ = devig_odds(odds_a, odds_b)
    raw_edge = model_probability - market_probability_a
    capped_edge = max(-MAX_REPORTED_EDGE, min(MAX_REPORTED_EDGE, raw_edge))
    return ValueFlag(
        model_probability=model_probability,
        market_probability=market_probability_a,
        edge=capped_edge,
        flagged=abs(capped_edge) >= FLAG_THRESHOLD,
    )
