# 7. Trading rules are hard constraints, not soft signals

- Status: Accepted
- Date: 2026-09-08

## Context

Margin, price bounds, suspension state and staleness checks exist to
prevent CourtEdge from ever serving a fabricated, stale or reckless price
(e.g. during a rain delay, or when a downstream layer fails). If these
checks could be weighed against or overridden by a blend weight, a
calibration adjustment, or the bounded value-detection nudge, a confident
but wrong upstream signal could push a bad price through anyway.

## Decision

Trading rules are applied as a final, non-negotiable gate: suspension,
price bounds and margin cannot be overridden by the blend, the calibration
layer, or the value-detection layer. The value-detection layer may only
flag a comparison for research purposes; it never alters the served
probability or price.

## Consequences

- Directly implements the "hard rules before soft signal" architecture
  principle and the "graceful degradation" principle (failure leads to a
  simpler honest method or a suspended quote, never a fabricated price).
- The failure-mode table's rule "Trading-rules service failure → suspend
  pricing entirely rather than guess a margin" only makes sense if trading
  rules are already the final authority when they are available.
- Scenario tests for suspension (rain delay, medical timeout) and staleness
  (late/missing point event) become required entries in the
  scenario-regression suite (charter target model scenarios), since this
  ADR makes them safety-critical rather than optional polish.
