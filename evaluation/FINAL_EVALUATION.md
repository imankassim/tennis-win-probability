# Final evaluation (Journey 21)

Synthesises every held-out result gathered across this project's run
experiments (EXP1 through EXP44 - not every number in that range was
actually run; EXP12 and EXP14, for instance, remain planned) into one
answer to the charter's own research question,
rather than a new, disjoint evaluation invented just for this journey -
see [docs/architecture/charter.md](../docs/architecture/charter.md) for
why: the "final held-out test" this journey calls for is what
[experiments/REGISTER.md](../experiments/REGISTER.md)'s full catalogue
already collectively represents. Every number below is real, reproduced
from its own experiment write-up - nothing here is newly computed for
this document alone except the promoted pipeline's own quality-eval
numbers (Journey 17/19/20).

## Research question

> To what extent does a machine-learned in-play win-probability model,
> blended with a transparent point-based Markov chain baseline and
> refined by a learned calibration step, improve probabilistic accuracy
> and calibration compared with the Markov baseline alone and with
> observed historical market prices?

## Answer

**Yes, against the Markov baseline - by a real but modest margin,
concentrated mostly in the ML step rather than the blend.** **No,
against the de-vigged market pre-match** - expected, and reported as
the honest result the charter's evidence rule requires, not a
disappointing one to soften.

## The evidence chain, in order

| Step | Configuration | Brier score | Log-loss | vs. previous step |
|---|---|---|---|---|
| Floor | EXP1 - always 50/50 | 0.2500 | 0.6931 | - |
| Primitive baseline | EXP2 - score-leader heuristic | 0.1934 | 0.5737 | 22.6% lower Brier than EXP1 |
| Analytic baseline | Markov (EXP10/11/13, shrunk serve rates) | 0.1839 | 0.5579 | 4.9% lower Brier than EXP2 |
| Learned candidate | ML alone (EXP24, LightGBM, state+context+momentum) | 0.1500 | 0.4540 | 15.1% lower Brier than Markov alone |
| Fusion, naive | EXP32 - fixed 50/50 blend | 0.1520 | 0.4617 | **worse than ML alone** - a real negative result, not noise |
| Fusion, tuned | **EXP33 - validation-tuned blend (markov_weight=0.15)** | **0.1490** | 0.4525 | 0.7% lower Brier than ML alone |
| Calibration | EXP43 - phase-level isotonic, applied to EXP33's output | 0.1511* | 0.4611* | 55% lower ECE than uncalibrated (0.0249 → 0.0113), on a different held-out split than the row above |
| **Promoted pipeline** | **blend_v1_calibrated, quality-eval slice** | **0.1481** | **0.4648** | Full pipeline, genuinely out-of-sample, real production numbers |
| External comparator | De-vigged market (EXP15, pre-match only) | 0.1828 | 0.5418 | **Beats this project's blend** (0.1984 pre-match) by a clear margin |

\* EXP40-43's Brier/log-loss are measured on a different held-out split
than EXP30-33's row above it (a final-test half specific to the
calibration experiments) - the two aren't a like-for-like sequential
comparison, only each one's own before/after story is. The promoted
pipeline's own quality-eval row is the number that actually matters for
"what does this system currently serve."

## What each step actually bought

- **Markov over the primitive heuristic**: a real, credible gap (4.9%
  lower Brier) once the archive was large enough that most players had
  genuine prior serve history - a near-tie on an earlier, smaller
  sample turned out to be a data-volume artifact, not evidence the
  Markov model doesn't help (see
  [experiments/EXP11-per-player-serve-rate.md](../experiments/EXP11-per-player-serve-rate.md)).
- **ML over Markov**: the single largest jump in the whole chain (15.1%
  lower Brier) - adding context (recent form, surface, head-to-head,
  Elo) and within-match momentum on top of raw score state clearly
  helps, and which features were included mattered far more than the
  choice between logistic regression and LightGBM on the same features
  (EXP20-23).
- **Blending Markov back in**: real, but the smallest gain in the
  chain, and the naive version (fixed 50/50) actively hurts (EXP32).
  Kept anyway - EXP33's tuned blend recovers a small edge, and,
  separately from the accuracy case, the architecture's
  graceful-degradation story (Journey 18) needs a blend that already
  leans on both estimators to have anywhere sensible to fall back to.
- **A learned meta-model instead of a fixed blend weight (EXP34)**:
  tried, rejected. Every variant underperformed the simple tuned blend,
  diagnosed as overfitting - 716,025 point-rows come from only 4,363
  independent matches, far less real signal for a many-parameter
  combiner than the row count suggests. The third instance in this
  project of "the fancier method loses" (after EXP23's representation
  comparison and EXP32's naive blend) - worth stating as a pattern, not
  three unrelated coincidences.
- **Calibration**: a genuine, large improvement in calibration error
  specifically (55% lower ECE) with a small accuracy improvement as a
  side effect, not the main point - Brier and log-loss are about
  *ranking* predictions correctly, ECE is about whether a "70%" quote
  is actually right 70% of the time; a system can improve one without
  the other; here both moved together, but that wasn't guaranteed
  (Platt scaling, tried on the same data, made ECE *worse* - EXP41).

## Against the market

The de-vigged market clearly beats this system pre-match (Brier 0.1828
vs 0.1984, favourite-picks-the-winner accuracy 73.9% vs 67.5% - see
[trading_rules/README.md](../trading_rules/README.md)). This is the
expected, honest result: real sportsbook prices incorporate injury
news, insider form and line movement this prototype has no access to,
and pre-match is the hardest comparison point for this system
specifically, since it's the one moment with zero in-play score-state
signal - only the context features are doing any work at all. The
context layers do measurably close the gap versus serve-rate-only
Markov (0.2305 → 0.1984 pre-match), which is itself real evidence those
features add value, just not enough to close a 15-point-Brier gap
against professionally-priced markets.

## Reliability and drift

Journey 18's failure-injection tests confirmed the graceful-degradation
architecture actually works, not just in design: an ML model failure or
a blend/calibration failure both correctly fall back to Markov-only
rather than crashing or serving a wrong number, distinguished by
whether the fallback margin widens (see
[docs/architecture/deployment.md](../docs/architecture/deployment.md)).
Journey 18's cross-era check (EXP44) found no sharp collapse between the
archive's 2010s and 2020s halves, but a real ~11% relative Brier gap
between them, honestly reported alongside the confound that makes it
not yet a clean drift measurement (the promotion script's split is by
recency, not by era).

## Limitations (see also docs/ethics/assessment.md)

- **Men's professional tennis only** - the WTA file was never ingested;
  nothing here should be assumed to generalise to women's tennis or
  other levels of play.
- **The cross-era drift check has a real methodological confound** -
  not yet a clean answer to "does this generalise across eras."
- **The blend's accuracy edge over ML alone is small** (0.7%) - most of
  this project's real gain over the Markov baseline comes from the ML
  layer, not from fusion.
- **No live feed exists** - every number here is computed by replaying
  static historical data; latency, quote logging and fallback behaviour
  are real and tested (Journeys 7, 18-19), but nothing in this project
  has been exercised against genuinely live, time-pressured traffic.

## Verdict

Retained as the leading, served configuration
(`model_version="blend_v1_calibrated"`), on the evidence above - a real,
reproducible improvement over the Markov baseline, an honestly-reported
loss against the external market benchmark, and a documented trail of
what was tried and rejected along the way (naive blending, Platt
scaling, the learned meta-model), matching the charter's evidence rule:
retained only because it solves a named problem, is reproducible, and
improves the agreed evidence without unacceptable cost - not because it
was the most sophisticated option tried.
