# Delivery roadmap

The journeys are intentionally ordered so each one creates a working or
testable foundation for the next. Rejected experiments remain documented
evidence.

## Journey roadmap

| Journey | Primary work | Exit outcome |
|---|---|---|
| 1. Investigation setup | Repository, experiment register, ADRs | A traceable project before implementation. |
| 2. First visible dashboard | Match selector, probability chart, page states | The dashboard defines the response contract. |
| 3. Primitive baselines | 50/50 and score-leader heuristics | Weak but measurable baselines. |
| 4. Data foundation | Matches, points, players, quality gates | Reliable source data. |
| 5. API | FastAPI health, probability and replay | A complete dashboard-to-Python path. |
| 6. Replay behaviour | Match detail, scenario library, filters | A testable replay journey. |
| 7. Instrumentation | Request IDs, model version, quote events | Traceable behaviour data. |
| 8. Evaluation | Outcome labels, Brier, log-loss, latency | Objective selection criteria. |
| 9. Markov baseline | Serve-rate estimation, recursive formula, tuning | Strong analytic baseline. |
| 10. Context features | Ranking, form, surface, h2h extraction | Safe structured context signals. |
| 11. ML probability model | Feature dataset, grouped splits, XGBoost/LightGBM | Data-driven candidate estimate. |
| 12. Blend | Weighted combination experiments | Combined analytic and learned estimate. |
| 13. Calibration & trading rules | Margin, suspension, calibration methods | Safe, well-calibrated final price. |
| 14. Learned meta-model | Stacked features, grouped splits, fallback | Learned combination of all signals. |
| 15. Bounded value-detection | Market-comparison feature, backtest with caps | Research-only insight layer. |
| 16. Optional extensions | Shot-level features, grounded explanation layer | Separate advanced investigations. |
| 17. Full API | Orchestration and response contract | Integrated pricing service. |
| 18. Reliability | Failure injection, sync and drift tests | Known failure behaviour. |
| 19. Dashboards | Quality, latency, errors and regressions | Observable evidence. |
| 20. Deployment | Containers, CI, monitoring and rollback | Repeatable release. |
| 21. Final evaluation | Held-out test, model card, data sheet, ethics | Defensible conclusion. |

## Work packages

| ID | Work package | Main outputs | Depends on |
|---|---|---|---|
| WP1 | Discovery and evidence design | Brief, research question, scenario taxonomy, metrics, risk register | None |
| WP2 | Front-end shell | Static replay dashboard, chart/ticker components, page states | WP1 |
| WP3 | Data foundation and API | DB schema, ingestion, validation, probability/replay endpoints | WP1, WP2 |
| WP4 | Replay behaviour | Playback controls, match-state parser, scenario library | WP3 |
| WP5 | Instrumentation and labels | Quote/event schema, request IDs, outcome labels, evaluation set | WP3, WP4 |
| WP6 | Markov baseline | Serve-rate estimation, recursive probability engine, tuning | WP3, WP5 |
| WP7 | Context features | Deterministic ranking, form, surface and h2h extraction | WP5, WP6 |
| WP8 | ML and blended probability | Feature dataset, ML model experiments, blend study | WP5, WP6, WP7 |
| WP9 | Calibration and trading rules | Calibration methods, margin/suspension/staleness rules | WP8 |
| WP10 | Learned meta-model | Stacked feature dataset, grouped splits, meta-model, fallback | WP5, WP8, WP9 |
| WP11 | Bounded value-detection | Market-comparison features, bounded flag, backtest with caps | WP4, WP10 |
| WP12 | Operations | Tests, failure injection, sync/drift checks, containers, CI | All prior serving work |
| WP13 | Final evidence | Held-out results, architecture, model card, data sheet, ethics review | WP12 |

## Stage decision gates

| Gate | Question | Continue when |
|---|---|---|
| G1: Dashboard | Is the replay and probability journey understandable with mock data? | Success, loading, error and suspended states are usable. |
| G2: Data | Can trusted match, point and player data be rebuilt? | Quality checks pass and provenance is recorded. |
| G3: API | Can the dashboard, Python and database exchange validated data? | Contract and integration tests pass. |
| G4: Evaluation | Can configurations be compared fairly? | Outcome labels, metric tests and match-level splits are frozen. |
| G5: Markov baseline | Is the analytic model a credible tuned baseline? | Validation and error-analysis evidence exists. |
| G6: ML model | Does the learned model add useful accuracy beyond the baseline? | Wins and losses are measured by match phase. |
| G7: Blend | Does combining Markov and ML improve on either alone? | It improves calibrated accuracy without unacceptable latency. |
| G8: Calibration & meta-model | Does the learned combination beat simpler blending? | Grouped validation improves and fallback works. |
| G9: Value-detection | Does the bounded layer add insight without overriding the price? | Behaviour remains reliable; no staking recommendation is produced. |
| G10: Release | Can the system be operated and restored? | Tests, monitoring, versioning, rollback and governance evidence are complete. |
| G11: Conclusion | Are the claims supported? | Held-out outputs, limitations and negative results are published. |

## Testing and acceptance matrix

| Test level | Examples | Acceptance intent |
|---|---|---|
| Unit | Markov formula, blend calculation, feature generation, margin/suspension rules. | Small functions behave exactly as defined. |
| Data quality | Unique IDs, monotonic sequence, valid server field, probability bounds. | Invalid data cannot silently enter serving. |
| API contract | Required response fields, input validation, model version, suspended flag. | Dashboard and back end share a stable contract. |
| Integration | Next.js to FastAPI, database read, probability computation, event write. | Components work together. |
| Scenario regression | Fixed break-point, decider, suspension and stale-data scenarios. | Known useful behaviour is protected. |
| Offline evaluation | Brier score, log-loss, calibration curve, match-phase breakdown. | Configuration choices are evidence-led. |
| Failure injection | Disable ML, blend, calibration or trading-rules components. | Fallback and suspension behaviour match the runbook. |
| Performance | Median and p95 latency under representative test conditions. | Quality is considered alongside serving behaviour. |
| Accessibility | Keyboard, focus, labels, alt text and contrast on the dashboard. | Primary journeys remain usable. |
| Security / privacy | Input validation, secret scan, licence-compliance check. | Prototype does not create avoidable risk. |
| User evaluation | Blind comparison of probability curves where appropriate. | Human usefulness complements offline metrics. |

## Minimum artefact set

- Project charter and scope.
- System context, logical, data, offline training and deployment architectures.
- Experiment register and architecture decision records.
- Match/player data sheet and provenance register.
- Outcome-label rubric and evaluation match set.
- Evaluation harness and saved result lists.
- Model card and feature schema.
- Testing evidence and failure-injection report.
- Monitoring dashboard and operational runbook.
- Ethics, privacy and responsible-gambling assessment.
- Final held-out evaluation and demonstration script.

## Potential Level 7 evidence mapping

The exact apprenticeship mapping should be checked against the current
assessment requirements. The following is a suggested evidence
relationship, not an assessment decision.

| Evidence theme | CourtEdge artefacts |
|---|---|
| AI and ML methods | Markov analytic baseline, ML win-probability model, blending, learned calibration and meta-model experiments. |
| Statistics and evaluation | Outcome-label design, Brier score, log-loss, calibration curves, grouped match-level splits, error analysis by phase. |
| Data engineering | Point-by-point ingestion, match/player/point schema, feature and replay store, quote-event pipeline, data-quality gates. |
| Software engineering | Next.js dashboard, FastAPI contract, tests, CI, containers, fallback behaviour. |
| Architecture and scalability | Online probability request path, offline training path, parallel Markov/ML computation, monitoring and deployment views. |
| Governance and ethics | Data provenance and licensing, privacy, access, explainability, bias monitoring, responsible-gambling framing, release controls. |
| Professional practice | ADRs, experiment register, technical documentation, stakeholder-facing demo, honest negative results. |
| Continuous development | Review of published tennis-forecasting literature, iterative experiments, documented learning checkpoints. |

## Current status

**Journeys 1–13 are complete.** Journey 10 (context features) was built
ahead of schedule by mistake between Journeys 6 and 7 — corrected rather
than hidden; the work itself is real and tested, just out of sequence.

Done so far:

- Repository scaffold, project charter, all architecture views, the
  decision records, the experiment register, data provenance rules and the
  risk register.
- A static Next.js replay dashboard (`frontend/`) running on two scripted
  mock matches, with all four target page states reachable: loading,
  success, error (unknown match), and a suspended quote mid-replay.
- The primitive baselines — always-50/50 and the current-score-leader
  heuristic (`EXP1`, `EXP2`, in `pricing/baselines/`) — as the weak,
  measurable floor every later component must clear.
- The data foundation (`database/`): a PostgreSQL schema for matches,
  players, points and outcome labels, and an ingestion pipeline for the
  [Match Charting Project](https://github.com/JeffSackmann/tennis_MatchChartingProject)
  (the originally-named data source had been removed from GitHub — see
  [decision 9](decisions/9-match-charting-project-data-source.md)). Run
  against the full 2010s+2020s archive: 5,453 matches / 890,356 points
  with a confirmed outcome, 115 correctly quarantined incomplete charts.
- A FastAPI backend (`backend/`) exposing `/health`, `GET /matches`,
  `/replay/{match_id}` and `/probability`, matching the documented
  response contract exactly, plus a real match-state parser for
  break-point detection.
- The frontend is wired to it: `/matches` browses and filters real
  ingested matches, replayed through the same components as the scenario
  library, which stays separate (mock data) since it demonstrates page
  states — suspension — a completed match archive can't produce.
- Instrumentation (`backend/event_log.py`): every served quote is logged
  as a JSONL record (request ID, model version, latency,
  fallback/suspended) to a plain analytical file, not a database.
- Evaluation (`evaluation/`): Brier score, log-loss and latency
  percentiles, plus a harness that scores any configuration against every
  point of every match with a confirmed outcome.
- The Markov baseline (`pricing/markov/`): the recursive point-to-match
  formulas (Klaassen & Magnus, 2003), serve-rate estimation with Bayesian
  shrinkage (EXP10/11/13), wired into `/probability` as `markov_v1`,
  replacing the score-leader placeholder. Real result on the full
  archive: beats EXP2 by 4.9% lower Brier score, 2.8% lower log-loss —
  widened from a marginal gap on an earlier, smaller sample once more
  history was ingested. See
  [pricing/markov/README.md](../pricing/markov/README.md) and
  [evaluation/README.md](../evaluation/README.md).
- Context features (`backend/context_features.py`): recent form, surface
  record and head-to-head from our own archive, no-look-ahead. Player
  strength (`backend/player_rating.py`): a self-computed Elo rating,
  since no external ranking feed was ever found — verified sensible
  against real data (top-rated players: Sinner, Alcaraz, Djokovic,
  Federer).
- The ML model (`pricing/ml/`): EXP20-24, logistic regression and
  LightGBM over increasing feature sets (state, +context, +momentum) on
  a chronological match-level held-out split. The leading candidate
  (EXP24, LightGBM with all three) beats Markov by 15.1% lower Brier
  score, 15.7% lower log-loss. Finding: which features are included
  mattered far more than model family (logistic vs LightGBM scored
  within noise of each other on the same features). Not yet wired into
  the live API — the architecture blends the Markov and ML estimates
  (Journey 12) rather than one replacing the other. See
  [pricing/ml/README.md](../pricing/ml/README.md).

- The blend (`pricing/blend/`): EXP30-33 on the same held-out data. A
  naive fixed 50/50 blend (EXP32) is *worse* than ML alone — a concrete
  demonstration that blending isn't automatically an improvement. Only a
  validation-tuned weight (EXP33, `markov_weight=0.15`) recovers a real,
  if modest, edge (0.7% lower Brier than ML alone). See
  [pricing/blend/README.md](../pricing/blend/README.md).
- Calibration and trading rules (`pricing/calibration/`,
  `trading_rules/`): EXP40-43 — isotonic regression clearly improves
  calibration error over the raw blend, phase-level isotonic improves it
  further (55% lower ECE), and Platt scaling (the "standard" method)
  actually makes it worse — a genuine negative result, kept as evidence.
  Trading rules (margin, price bounds, suspension) are wired into the
  live API: `suspended` is now genuinely computed, not always false. See
  [pricing/calibration/README.md](../pricing/calibration/README.md) and
  [trading_rules/README.md](../trading_rules/README.md).

Next: **Journey 14** (the learned meta-model — stacking Markov output, ML
output and features, with fallback).

## Source

Derived from `docs/CourtEdge_Architecture_and_Task_Definition.docx`,
sections 12, 13, 15, 17, 18 and 19.
