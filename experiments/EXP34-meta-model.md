# EXP34 — Stacked meta-model combining Markov output, ML output and features

- Status: Rejected (retained as evidence) — EXP33's simple tuned blend remains the leading configuration
- Depends on: EXP24, EXP33
- Date: 2026-09-08

## Hypothesis

A learned combiner — fed the Markov and ML outputs alongside the raw
score-state/context/momentum features — should beat a fixed-formula
weighted average (EXP33), since it can in principle learn
context-dependent combination rules a single scalar weight can't (e.g.
"trust Markov more in the deciding set").

## Configuration

`pricing/blend/meta_model.py::MetaModel` — logistic regression (with
feature scaling) over `[markov_prediction, ml_prediction] +
STATE_FEATURES + CONTEXT_FEATURES + MOMENTUM_FEATURES`, trained on the
same training set as EXP20-24/EXP24, evaluated on the same final-test
set as EXP30-33.

## Metrics

| Configuration | Brier score | Log-loss |
|---|---|---|
| EXP33 (tuned blend, comparator) | 0.1518 | 0.4587 |
| EXP34, logistic, full features, C=1.0 (default) | 0.1860 | 0.5858 |
| EXP34, logistic, full features, C=0.001 (strong L2) | 0.1777 | 0.5510 |
| EXP34, logistic, markov+ml only (no raw features) | 0.1687 | 0.5202 |
| EXP34, LightGBM meta, full depth (`n_estimators=100, max_depth=6`) | 0.1867 | 0.5743 |
| EXP34, LightGBM meta, shallow (`n_estimators=50, max_depth=3`) | 0.1622 | 0.4892 |

**Finding: every variant tried underperforms the simple tuned blend —
some of them badly.** This was investigated rather than accepted at
first sight (the default logistic version, at 0.1860, was *worse than
Markov alone*, which shouldn't happen if a stacking model is working
correctly — that specifically prompted the extra variants below it).

Diagnosis: the default model's `markov_prediction` coefficient came out
**negative** (-0.67) — backwards, since a higher Markov estimate should
never be associated with a *lower* combined probability. That's the
signature of multicollinearity: `markov_prediction` and `ml_prediction`
are highly correlated (both estimate the same underlying quantity), and
adding 15 further raw features that are themselves inputs to
`ml_prediction` compounds it. Stronger regularisation and shallower trees
both partially recover performance (the shallow LightGBM's 0.1622 is far
closer to EXP33 than the unregularised versions), confirming
**overfitting**, not a data or wiring bug, is the root cause — and a
specific reason for it: 716,025 training point-rows come from only 4,363
independent matches. Points within one match share the same label and
nearly-identical context features, so the *effective* sample size for
learning a stable combination rule is much closer to "a few thousand"
than "seven hundred thousand" — plenty for a single tuned scalar weight
(EXP33), not enough for a many-parameter learned combiner to generalise
reliably.

## Decision

**Rejected as a candidate — EXP33 remains the leading blend
configuration.** Kept as evidence rather than discarded: it's a genuine,
diagnosed negative result (not "we didn't try hard enough" — six
variants were tried), and it extends a pattern this project keeps
finding (EXP23's representation comparison, EXP32's naive blend, EXP41's
Platt scaling): a more sophisticated method is not automatically a
better one, and the evidence rule exists precisely so it doesn't get
promoted just for looking more sophisticated.

**Fallback behaviour (the other half of this journey's scope) is still
useful and retained independent of the model comparison above.**
`predict_with_fallback()` degrades to Markov-only or ML-only if either
base estimate is missing — that logic doesn't depend on which combiner
wins, and stays ready for whichever blend configuration is actually
served.

**Follow-up, not done:** a match-grouped cross-validation scheme (so the
meta-learner is evaluated the way its effective sample size actually
behaves) might tell a more forgiving story than a single train/test
split does — worth trying if this is revisited.
