# trading_rules

Margin, price bounds, suspension state, staleness checks and bounded
value-flagging. Hard rules that cannot be overridden by a blend weight,
calibration adjustment or value-detection nudge.

## Status

Journeys 13 and 15 are both complete.

## Structure

- `rules.py` — `apply_trading_rules(probability_a)`: the final gate.
  Applies margin (`DEFAULT_MARGIN = 0.05`) and returns prices, or
  suspends (both prices `None`) if the probability is missing, outside
  [0, 1], exactly 0 or 1 (an undefined price), or if the computed price
  falls outside a sanity bound (`MAX_REASONABLE_PRICE`). `is_stale()` is a
  tested, ready-to-wire staleness check — not yet meaningful, since this
  system replays static historical data rather than a live feed
  (see docs/architecture/charter.md's "what will not be built"). Wired
  into `backend/main.py`'s `/probability` handler: `suspended` is
  genuinely computed rather than always `false`.
- `value_detection.py` — `devig_odds()` (removes the bookmaker's
  overround) and `compute_value_flag()` (compares a model probability
  against the de-vigged market price, with a **capped** edge —
  `MAX_REPORTED_EDGE = 0.15`, since a larger disagreement almost always
  signals a data problem, not a genuine mispricing — and a boolean flag
  only past `FLAG_THRESHOLD = 0.05`). Never called from the live pricing
  path; strictly an offline research comparison, and the flag never
  alters a served price.

## Real evidence (the value-detection backtest, Journey 15)

Real 2025-2026 ATP odds (`database/ingestion/tennis_data_co_uk.py`,
average closing odds across bookmakers) matched to our own ingested
archive by player surname and date — 621 matches with both a confirmed
outcome and matched market odds, out of 638 total matches matched (some
lacked a confirmed outcome in our own data). Pre-match (before any point
is played) Brier score, our models vs. the de-vigged market:

| Source | Brier score | Log-loss |
|---|---|---|
| Markov (serve rates only) | 0.2305 | 0.6541 |
| ML (EXP24) | 0.1988 | 0.5787 |
| Blend (EXP33) | 0.1984 | 0.5780 |
| **De-vigged market** | **0.1828** | **0.5418** |

Favourite-picks-the-winner accuracy: our blend 67.5%, the market 73.9%.

**The market wins, clearly — and that's the expected, honest result, not
a disappointing one.** Real sportsbook prices incorporate far more
information than this prototype has access to (injury news, insider
form, line movement, a much larger and more current data pool), and
pre-match is the hardest comparison for us: it's the one point in a
match where we have no in-play score-state signal at all, only the
context features. Per the risk register's own "market-odds benchmark
limitations" mitigation, this is reported as a research comparison, not
a "beat the market" claim — none was made or expected. The
context-feature layers (ML, blend) do meaningfully close the gap
compared to serve-rate-only Markov alone (Brier improves from 0.2305 to
0.1984), which is itself useful evidence that those features are adding
real, if not market-beating, predictive value.

Run it yourself: download a yearly file from
[tennis-data.co.uk/alldata.php](http://tennis-data.co.uk/alldata.php)
(e.g. `2026/2026.xlsx`), then use
`database.ingestion.tennis_data_co_uk.parse_market_odds` and
`match_market_odds_to_archive` to match it to your own ingested matches.
