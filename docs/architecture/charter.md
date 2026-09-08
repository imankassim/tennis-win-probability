# Project charter and scope

## What CourtEdge is

CourtEdge is an original in-play tennis probability and pricing research
prototype, inspired by the type of real-time pricing systems used by sports
betting companies. It is not a copy of any real bookmaker's product, brand or
proprietary pricing feed, and it is not a real-money trading system.

Its purpose is to investigate whether a machine-learned in-play win-probability
model, combined with a transparent point-based analytic baseline, can produce
better-calibrated probabilities than the analytic baseline alone, and to
demonstrate the engineering architecture that a production in-play pricing
service would need.

## Primary research question

> To what extent does a machine-learned in-play win-probability model,
> blended with a transparent point-based Markov chain baseline and refined by
> a learned calibration step, improve probabilistic accuracy and calibration
> compared with the Markov baseline alone and with observed historical market
> prices?

## Problem, by dimension

| Dimension | Definition |
|---|---|
| User problem | A viewer or analyst wants to understand how a live match's win probability should move as points are played, and whether that movement is reasonable given the score, the players and the context. |
| Technical problem | Recompute a probability and an indicative price after every point, quickly enough for a live feed, without violating trading rules such as suspension, margin and price bounds. |
| ML problem | Learn how to combine an analytic point-based model with contextual and momentum signals while avoiding look-ahead leakage, sparse-data overclaiming and overreaction to small samples. |
| Operational problem | Serve probabilities reliably, record model and calibration versions, monitor quality and latency, and fall back to a simpler transparent method when advanced components fail. |
| Evidence problem | Demonstrate improvement using held-out match outcomes, repeatable experiments, error analysis by match phase, and a final held-out test set. |

## Scope

### What will be built

- An original replay and pricing dashboard called CourtEdge.
- A match, point and player catalogue built from permitted public tennis data.
- A Next.js front end for match replay, a live probability chart, a price ticker and scenario browsing.
- A Python FastAPI back end that exposes probability, price, replay and event endpoints.
- A PostgreSQL transactional source of truth for matches, players, points and outcome labels.
- A DuckDB or Parquet feature-and-replay store supporting fast, point-in-time feature computation.
- A transparent Markov chain analytic engine for point-to-match win probability.
- A machine-learned win-probability model (XGBoost or LightGBM) using state and context features.
- A validated blending layer and a learned meta-model combining the analytic and ML estimates.
- A calibration layer mapping blended probability onto empirically observed outcome frequencies.
- A trading-rules layer applying margin, price bounds, suspension and staleness checks.
- A bounded, clearly labelled research-only market-comparison layer.
- An evaluation and monitoring layer for accuracy, calibration, reliability, latency and fallback behaviour.

### What will not be built initially

- Real-money wagering, payments, settlement, or any regulated betting operation.
- A copy of any real bookmaker's branding, proprietary pricing feed, or copyrighted content.
- A production-scale customer identity, KYC or account platform.
- Unrestricted LLM control of prices, trading rules or suspension logic.
- An advanced shot-level or biometric model promoted without sufficient genuine data.
- Automatic retraining or model promotion without review and governance.
- Live ingestion of a paid or restricted-licence data feed without confirmed usage rights.
- Any output presented as betting advice or a staking recommendation.

## Target model scenarios

These scenarios define the behaviour the whole pricing pipeline (Markov →
ML → blend → calibration → trading rules) is expected to handle sensibly,
and they seed the fixed scenario-regression test suite in
[tests/scenario_regression](../../tests/scenario_regression).

| Scenario | Example | System responsibility |
|---|---|---|
| Routine hold | Server leads 40–15 on serve | Track score without state drift; probability should move smoothly, not jump. |
| Break-point pressure | Break point against the favourite, second set | Blend must react proportionally to one point, not overreact to it. |
| Deciding-set recovery | Two sets to love down in a best-of-five | Model must reflect historical recovery base rates, not point maths alone. |
| Suspension | Rain delay or medical timeout | Trading rules must suspend pricing rather than serve a stale or guessed value. |
| Momentum shift | Momentum swings after a long rally or injury scare | An optional context feature may nudge the estimate but never override calibration. |
| Favourite under early pressure | Strong favourite trails early against a big outsider | Model should not overreact to a small-sample early lead against a strong prior. |
| Data gap | A point event arrives late or is missing | System must flag staleness rather than silently serving an outdated probability. |

## Success measures

### Evaluation measures

- Brier score for overall probabilistic accuracy.
- Log-loss for penalised probabilistic accuracy.
- Calibration error (ECE) and reliability diagrams.
- A de-vigged comparison against historical closing market prices, framed strictly as research validation, not as betting guidance.
- Median and p95 API latency for a probability request.
- Fallback rate and stale-quote rate.
- Error broken down by match phase (early, mid, late, deciding set) and by context (favourite versus underdog, surface), rather than average-only reporting.

### Functional requirements

| ID | Requirement | Evidence |
|---|---|---|
| FR-01 | A viewer can select a match and replay it point by point while the system returns a live win probability and price. | End-to-end replay test and screen recording. |
| FR-02 | A viewer can see the applied margin and whether the quote is currently suspended. | API contract test covering margin and suspended fields. |
| FR-03 | The system can run Markov-only, ML-only, blended and calibrated configurations as separate experiments. | Saved configurations and outputs. |
| FR-04 | Every probability response includes a request ID and a model/configuration version. | API contract test. |
| FR-05 | Quote and replay events can be recorded without collecting unnecessary personal data. | Event schema and privacy review. |
| FR-06 | The blend can fall back to the Markov baseline, and the API can fall back to a suspended state, if any downstream layer fails. | Failure-injection tests. |
| FR-07 | Metrics can be calculated from saved match outcomes and quote logs alone. | Repeatable evaluation harness. |

### Non-functional requirements

| Area | Requirement |
|---|---|
| Accuracy | Performance is reported using held-out match outcomes and phase-of-match breakdowns, not favourable examples alone. |
| Reliability | A failure in the ML, blend or calibration layer must not prevent the Markov baseline from serving where it remains available. |
| Latency | Median and p95 response times are measured and reported. Thresholds are set from prototype evidence, not invented in advance. |
| Security | Secrets remain outside source code; interfaces validate inputs; deployed environments follow applicable approval requirements. |
| Privacy | Uses only public match and player data. No real user wagering or financial data is collected. Dashboard analytics, if any, are anonymous and purposeful. |
| Accessibility | Keyboard navigation, labels, focus states, alt text and colour contrast are included on the dashboard. |
| Maintainability | Components are modular, versioned and covered by unit, integration and regression tests. |
| Auditability | Requests, outputs, configurations and model/calibration versions can be traced without logging unnecessary content. |
| Cost | Compute and infrastructure costs are measured where available and discussed alongside quality. |
| Responsible framing | The system is clearly labelled as a research prototype. It must never be presented as betting advice or a staking recommendation. |

## Evidence rule

No experiment is promoted because it looks more sophisticated. It remains
only if it solves a named problem, is reproducible, and improves the agreed
evidence without creating unacceptable latency, instability or ethical risk.

## Prototype boundary

This architecture is a technical learning and portfolio design. It does not
constitute a compliant real-money betting system, and no part of it should be
deployed against real markets or real customers without full legal,
regulatory and responsible-gambling review.

## Source

Derived from `docs/CourtEdge_Architecture_and_Task_Definition.docx`,
sections 1–3.
