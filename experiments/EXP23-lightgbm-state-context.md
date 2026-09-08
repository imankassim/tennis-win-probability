# EXP23 — XGBoost/LightGBM classifier, state and context features

- Status: Retained
- Depends on: EXP21, EXP22
- Date: 2026-09-08

## Hypothesis

Combining what EXP21 (context helps) and EXP22 (trees help a little)
each showed should compound: LightGBM should extract more from the
context features than logistic regression could, via feature
interactions (e.g. Elo gap mattering differently depending on surface).

## Configuration

Same features as EXP21 (state + context), LightGBM instead of logistic
regression. Same train/test split.

## Metrics

| Configuration | Brier score | Log-loss |
|---|---|---|
| Markov (comparator) | 0.1839 | 0.5579 |
| EXP21 (logistic, state + context) | 0.1597 | 0.4796 |
| EXP23 (LightGBM, state + context) | 0.1596 | 0.4790 |

**Finding, not the expected one:** EXP23 barely beats EXP21 (a 0.0001
Brier difference — noise-level, not a real gap). The hypothesis that
trees would extract materially more from the context features than a
linear model was not confirmed. Read together with EXP22 (trees only
edge out logistic on state-only by 1.0%), the pattern is that **model
family matters far less here than which features are included** — the
state→context→outcome relationship this data expresses is close to
linear, at least with the features built so far. This is a genuine
negative-ish result, kept rather than glossed over: it doesn't mean
LightGBM was the wrong choice (EXP24 below shows it still has room to
add value via momentum), but it means "just add more powerful models" is
not, on this evidence, where the accuracy gains are coming from.

## Decision

Retained as the direct comparator for EXP24. The representation
comparison result (family matters little; features matter a lot) is
itself useful evidence for where to spend effort next — more/better
features over a fancier model, all else equal.
