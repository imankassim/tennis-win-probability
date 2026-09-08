# pricing/blend

Fusion of the Markov analytic estimate and the ML estimate: weighted
combination experiments (Journey 12) and the learned meta-model
(Journey 14).

## Status

Journeys 12 and 14 are complete. `blend.py` — `blend_probability()` (a
plain weighted average) and `tune_weight()` (sweeps the weight on a
validation set, never the final test set) — EXP33 is the leading
configuration. `meta_model.py` — `MetaModel` (a learned stacking
combiner) and `predict_with_fallback()` — EXP34 was rejected (the learned
combiner overfits and underperforms EXP33's simple tuned weight; see
below), but the fallback logic is retained and ready regardless of which
combiner is served. Not yet wired into the live API — the leading
candidates (EXP24 ML, EXP33 blend, EXP43 calibration) wait for a
deliberate decision to change what `/probability` serves, not an
automatic promotion.

## Real evidence

On a held-out final-test slice (88,305 points / 545 matches, split off
from Journey 11's test set — the other half tuned EXP33's weight):

| Configuration | Brier score | Log-loss |
|---|---|---|
| EXP30 — Markov-only | 0.1686 | 0.5061 |
| EXP31 — ML-only (EXP24) | 0.1500 | 0.4540 |
| EXP32 — fixed 50/50 blend | 0.1520 | 0.4617 |
| **EXP33 — tuned blend (markov_weight=0.15)** | **0.1490** | **0.4525** |

**Finding worth knowing before assuming blending always helps: the naive
50/50 blend (EXP32) is *worse* than ML alone (EXP31).** Averaging a
clearly stronger model with a clearly weaker one at equal weight drags
the result down. Only the validation-tuned weight (EXP33 — landed on
mostly trusting ML, `markov_weight=0.15`) recovers an improvement, and
even then it's modest (0.7% lower Brier than ML alone). Kept anyway,
partly for that real if small edge, and partly because the architecture's
graceful-degradation story (falling back toward Markov if the ML model
becomes unavailable) needs a blend that already leans on both, not a
switch that's effectively ML-only. See
[EXP32-EXP33-blend.md](../../experiments/EXP32-EXP33-blend.md) for the
full finding.

## Real evidence (the meta-model, EXP34)

The learned meta-model was rejected: every variant tried (logistic
regression at several regularisation strengths, LightGBM at several
depths) underperformed EXP33's simple tuned blend, some badly — the
unregularised default even scored *worse than Markov alone*. Diagnosed,
not just observed: 716,025 training point-rows come from only 4,363
independent matches, so the effective sample size for learning a stable
combination rule is far smaller than the row count suggests — enough for
a single tuned scalar weight, not enough for a many-parameter learned
combiner. See [EXP34-meta-model.md](../../experiments/EXP34-meta-model.md)
for the full investigation.
