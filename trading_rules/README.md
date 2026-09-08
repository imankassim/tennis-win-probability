# trading_rules

Margin, price bounds, suspension state, staleness checks and bounded
value-flagging. Hard rules that cannot be overridden by a blend weight,
calibration adjustment or value-detection nudge.

## Status

Journey 13 (margin, price bounds, suspension) is complete and wired into
the live API — see `rules.py`. Bounded value-flagging is Journey 15, not
yet built.

## Structure

- `rules.py` — `apply_trading_rules(probability_a)`: the final gate.
  Applies margin (`DEFAULT_MARGIN = 0.05`) and returns prices, or
  suspends (both prices `None`) if the probability is missing, outside
  [0, 1], exactly 0 or 1 (an undefined price), or if the computed price
  falls outside a sanity bound (`MAX_REASONABLE_PRICE`). `is_stale()` is a
  tested, ready-to-wire staleness check — not yet meaningful, since this
  system replays static historical data rather than a live feed
  (see docs/architecture/charter.md's "what will not be built").

Wired into `backend/main.py`'s `/probability` handler: `suspended` is now
genuinely computed rather than always `false`, and
`probability_player_a` is `null` whenever a quote is suspended, matching
the documented response contract.
