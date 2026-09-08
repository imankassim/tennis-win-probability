"""The trading rules layer (Journey 13): margin, price bounds, and
suspension/staleness checks.

Per decision 7 (docs/decisions/7-trading-rules-as-hard-constraints.md):
these are hard constraints, not soft signals — they cannot be overridden
by a blend weight, a calibration adjustment, or a value-detection nudge,
and this is the final gate before a probability response is returned. A
failure anywhere upstream (a missing, invalid, or out-of-bounds
probability) must produce a suspended quote here, never a fabricated
price — the same principle backend/probability.py's margin logic
followed as a placeholder from Journey 5 onward; this is its real home
and its real implementation.
"""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_MARGIN = 0.05
MIN_VALID_PRICE = 1.0
# A sanity cap, not a real trading limit: a computed price this high means
# something upstream is almost certainly wrong (a probability vanishingly
# close to 0 or 1), not a plausible quote worth serving as-is.
MAX_REASONABLE_PRICE = 1000.0
# Meaningful once a live feed exists — this system replays static
# historical data today (docs/architecture/charter.md's "what will not be
# built"), so nothing currently produces a data_age_seconds to check. Kept
# as a tested, ready-to-wire pure function rather than left unbuilt.
DEFAULT_MAX_STALENESS_SECONDS = 30.0


@dataclass(frozen=True)
class TradingResult:
    price_a: float | None
    price_b: float | None
    suspended: bool
    reason: str | None


def price_from_probability(probability: float, margin: float = DEFAULT_MARGIN) -> float:
    return round(1 / (probability * (1 + margin)), 2)


def apply_trading_rules(
    probability_a: float | None, margin: float = DEFAULT_MARGIN
) -> TradingResult:
    """The final gate: given an upstream probability (which may be None,
    or out of [0, 1], if an earlier layer failed), decide the served
    price or suspend. A probability of exactly 0.0 or 1.0 is treated as
    unpriceable (the corresponding price would be undefined/infinite),
    not as a valid input needing a boundary-case price."""
    if probability_a is None or not (0.0 < probability_a < 1.0):
        return TradingResult(None, None, True, "missing, invalid, or unpriceable probability")

    price_a = price_from_probability(probability_a, margin)
    price_b = price_from_probability(1 - probability_a, margin)

    if not (MIN_VALID_PRICE <= price_a <= MAX_REASONABLE_PRICE) or not (
        MIN_VALID_PRICE <= price_b <= MAX_REASONABLE_PRICE
    ):
        return TradingResult(None, None, True, "computed price outside acceptable bounds")

    return TradingResult(price_a, price_b, False, None)


def is_stale(
    data_age_seconds: float, max_age_seconds: float = DEFAULT_MAX_STALENESS_SECONDS
) -> bool:
    """True if the point data behind a quote is older than
    max_age_seconds."""
    return data_age_seconds > max_age_seconds
