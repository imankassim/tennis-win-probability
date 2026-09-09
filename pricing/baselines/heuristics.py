"""Primitive baselines (EXP1, EXP2) - see experiments/REGISTER.md.

These exist as the weak floor every later component (the Markov baseline,
the ML model, the blend) must clear. They are deliberately not tuned or
improved: their value is in being obviously, measurably weak, so any later
"improvement" claim has something honest to be better than.

Full accuracy metrics against held-out match outcomes are deferred to
Journey 8 (evaluation), once the outcome-label set and evaluation harness
exist. For now these are exercised by unit tests on constructed score
states only.
"""


def always_fifty_fifty() -> float:
    """EXP1 - ignores all match state and always returns 0.5.

    Known failure: carries zero information. Never wrong on average across
    a symmetric field, but never useful for a single match either - the
    absolute floor.
    """
    return 0.5


def score_leader_probability(sets_a: int, sets_b: int, games_a: int, games_b: int) -> float:
    """EXP2 - whoever currently leads gets a fixed probability bump: a set
    lead is worth more than a game lead, and ties fall back to 0.5.

    Known failures (see docs/architecture/charter.md's target model
    scenarios):
    - Ignores who is serving, so it misprices routine holds and break
      points identically.
    - The fixed bump is a discontinuous jump, not a smooth reaction, so it
      overreacts to a single game in a break-point-pressure scenario.
    - Has no concept of historical recovery base rates, so it misprices a
      deciding-set recovery.
    - Ignores ranking, form and surface entirely, so it misprices a
      favourite trailing early against a big outsider.
    """
    if sets_a != sets_b:
        return 0.75 if sets_a > sets_b else 0.25
    if games_a != games_b:
        return 0.6 if games_a > games_b else 0.4
    return 0.5
