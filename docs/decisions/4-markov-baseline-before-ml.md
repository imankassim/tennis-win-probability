# 4. Build a transparent Markov chain baseline before any learned model

- Status: Accepted
- Date: 2026-09-08

## Context

The primary research question asks whether a machine-learned model, blended
with a transparent analytic baseline, improves on the baseline alone. That
question is unanswerable without first establishing a credible, well-tuned
baseline to improve on — and without one, any later ML result is
unfalsifiable ("better than what?").

## Decision

Implement primitive baselines (always-50/50, score-leader heuristic, EXP1–2)
and then a point-based Markov chain analytic engine (EXP10–14, journey 9)
before starting any learned probability model (journey 11). The ML model is
evaluated against the tuned Markov baseline, not against the primitive
baselines.

## Consequences

- Gate G5 ("is the analytic model a credible tuned baseline?") must pass
  before gate G6 (the ML model) is attempted.
- The Markov engine remains in the serving path permanently as the fallback
  when the ML model, blend, or calibration layer is unavailable (see
  [docs/architecture/deployment.md](../architecture/deployment.md)), so it
  cannot be treated as throwaway scaffolding.
- Follows the "baseline first" architecture principle: every later layer
  (ML, blend, calibration, trading rules) is judged against whether it
  improves on the last accepted stage, not in isolation.
