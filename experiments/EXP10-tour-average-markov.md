# EXP10 - Constant tour-average serve rate Markov chain

- Status: Retained
- Depends on: EXP1, EXP2
- Date: 2026-09-08

## Hypothesis

A proper point-to-match recursive model (Klaassen & Magnus), even fed
nothing but a single constant serve-win rate for every player, should
capture score-state dynamics (break points, deciding sets, tiebreaks) that
the primitive score-leader heuristic (EXP2) can't - because EXP2 has no
concept of *how* points translate into games and sets, only "who's ahead".

## Configuration

`pricing/markov/formulas.py` (the recursive game/tiebreak/set/match
formulas) fed a single `tour_average_serve_rate()` (from
`pricing/markov/serve_rate.py`) for both players - no per-player
differentiation at all. This isolates the value of the *recursive
structure* itself, independent of serve-rate estimation quality (that's
EXP11/EXP13's job).

## Metrics

Not separately evaluated - EXP10 (constant rate) is a component of the
combined engine evaluated in EXP11/EXP13 below (with per-player,
then shrunk, serve rates), which is what's actually wired into the API.
Isolating EXP10 alone would require re-running `evaluation/evaluate_markov.py`
with `tour_average_serve_rate` substituted for `serve_rate_with_shrinkage`
in `pricing/markov/engine.py::estimate_match_serve_rates` - left as a
follow-up if the EXP11/EXP13 result ever needs decomposing further.

## Decision

Retained as the foundation EXP11 and EXP13 build on. The recursive
formulas themselves are verified independently of any real match data -
see `tests/unit/test_markov_formulas.py`, including a property (who serves
first doesn't matter from a fresh set) confirmed by an independent Monte
Carlo simulation, not just the recursion agreeing with itself.
