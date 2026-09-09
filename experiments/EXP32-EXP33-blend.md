# EXP32 / EXP33 - Fixed-weight and validation-tuned blend

- Status: EXP32 retained as evidence (a negative-ish result); EXP33 retained as the leading configuration
- Depends on: EXP30, EXP31
- Date: 2026-09-08

## Hypothesis

Combining the Markov and ML estimates should beat either alone - the
premise of the whole blend layer in the architecture.

## Configuration

`pricing/blend/blend.py::blend_probability(markov_p, ml_p, markov_weight)`
- a plain weighted average. EXP32 uses a fixed `markov_weight=0.5`.
EXP33 tunes the weight (`tune_weight`, 0.05 steps from 0.0 to 1.0) on the
validation half of the held-out set, then evaluates the chosen weight on
the final-test half - never tuning against the same data the result is
reported on.

## Metrics

On the final-test half (same 88,305 points / 545 matches as EXP30/31):

| Configuration | Brier score | Log-loss |
|---|---|---|
| EXP30 (Markov-only) | 0.1686 | 0.5061 |
| EXP31 (ML-only, EXP24) | 0.1500 | 0.4540 |
| EXP32 (fixed 50/50 blend) | 0.1520 | 0.4617 |
| **EXP33 (tuned blend, markov_weight=0.15)** | **0.1490** | **0.4525** |

**Finding, and it's not the expected one: the naive 50/50 blend (EXP32)
is *worse* than just using ML alone (EXP31).** Averaging a clearly
stronger model (ML) with a clearly weaker one (Markov) at equal weight
drags the result down, not up - a concrete demonstration of why "blend
the models" isn't automatically an improvement, and why the evidence rule
exists ("no experiment is promoted because it looks more sophisticated").

The tuned blend (EXP33) does recover an improvement - the weight search
on the validation set landed on `markov_weight=0.15` (mostly trust ML,
give Markov a small say), and that weight generalises to the final test
set: a real, if modest, edge over ML alone (0.7% lower Brier, 0.3% lower
log-loss).

## Decision

**EXP32 retained as evidence, not as a candidate** - the negative result
itself is the useful output: it shows *why* the weight needs tuning
rather than guessing something reasonable-sounding like 0.5.

**EXP33 retained as the leading configuration.** The accuracy edge over
ML alone is small on this evidence, which is worth being honest about -
a stricter reading of the evidence rule could reasonably ask whether a
0.7% Brier improvement justifies a second model's operational
complexity. Two things beyond the raw number justify keeping it here:
it's a real (not noise-level, unlike EXP21-vs-EXP23's representation
comparison) improvement confirmed on a held-out set the weight was never
tuned against; and the architecture's own rationale for a blend layer is
partly about **graceful degradation** (docs/architecture/deployment.md's
fallback table: if the ML model becomes unavailable, serving falls back
toward Markov-only) - a blend that already leans mostly on ML but keeps
Markov in the mix is exactly the shape that failure-recovery story
needs, not just an accuracy play.

**Not yet wired into the live API** - like EXP24, this is Journey 12's
candidate for what the calibration and trading-rules layer (Journey 13)
will build on, not a change to the currently-served `markov_v1`.
