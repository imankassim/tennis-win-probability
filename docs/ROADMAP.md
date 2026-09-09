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

**Journeys 1–21 are complete.** Journey 10 (context features) was built
ahead of schedule by mistake between Journeys 6 and 7 - corrected rather
than hidden; the work itself is real and tested, just out of sequence.
Journey 16 (optional extensions) is deliberately deferred - it's
explicitly optional in the source spec itself - in favour of the
non-optional Journeys 17-21, circling back only if time allows.

Done so far:

- Repository scaffold, project charter, all architecture views, the
  decision records, the experiment register, data provenance rules and the
  risk register.
- A static Next.js replay dashboard (`frontend/`) running on two scripted
  mock matches, with all four target page states reachable: loading,
  success, error (unknown match), and a suspended quote mid-replay.
- The primitive baselines - always-50/50 and the current-score-leader
  heuristic (`EXP1`, `EXP2`, in `pricing/baselines/`) - as the weak,
  measurable floor every later component must clear.
- The data foundation (`database/`): a PostgreSQL schema for matches,
  players, points and outcome labels, and an ingestion pipeline for the
  [Match Charting Project](https://github.com/JeffSackmann/tennis_MatchChartingProject)
  (the originally-named data source had been removed from GitHub - see
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
  states - suspension - a completed match archive can't produce.
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
  archive: beats EXP2 by 4.9% lower Brier score, 2.8% lower log-loss -
  widened from a marginal gap on an earlier, smaller sample once more
  history was ingested. See
  [pricing/markov/README.md](../pricing/markov/README.md) and
  [evaluation/README.md](../evaluation/README.md).
- Context features (`backend/context_features.py`): recent form, surface
  record and head-to-head from our own archive, no-look-ahead. Player
  strength (`backend/player_rating.py`): a self-computed Elo rating,
  since no external ranking feed was ever found - verified sensible
  against real data (top-rated players: Sinner, Alcaraz, Djokovic,
  Federer).
- The ML model (`pricing/ml/`): EXP20-24, logistic regression and
  LightGBM over increasing feature sets (state, +context, +momentum) on
  a chronological match-level held-out split. The leading candidate
  (EXP24, LightGBM with all three) beats Markov by 15.1% lower Brier
  score, 15.7% lower log-loss. Finding: which features are included
  mattered far more than model family (logistic vs LightGBM scored
  within noise of each other on the same features). Not yet wired into
  the live API - the architecture blends the Markov and ML estimates
  (Journey 12) rather than one replacing the other. See
  [pricing/ml/README.md](../pricing/ml/README.md).

- The blend (`pricing/blend/`): EXP30-33 on the same held-out data. A
  naive fixed 50/50 blend (EXP32) is *worse* than ML alone - a concrete
  demonstration that blending isn't automatically an improvement. Only a
  validation-tuned weight (EXP33, `markov_weight=0.15`) recovers a real,
  if modest, edge (0.7% lower Brier than ML alone). See
  [pricing/blend/README.md](../pricing/blend/README.md).
- Calibration and trading rules (`pricing/calibration/`,
  `trading_rules/`): EXP40-43 - isotonic regression clearly improves
  calibration error over the raw blend, phase-level isotonic improves it
  further (55% lower ECE), and Platt scaling (the "standard" method)
  actually makes it worse - a genuine negative result, kept as evidence.
  Trading rules (margin, price bounds, suspension) are wired into the
  live API: `suspended` is now genuinely computed, not always false. See
  [pricing/calibration/README.md](../pricing/calibration/README.md) and
  [trading_rules/README.md](../trading_rules/README.md).
- The learned meta-model (`pricing/blend/meta_model.py`): EXP34 -
  rejected. A learned combiner (stacking Markov + ML outputs with the raw
  features) underperformed the simple tuned blend (EXP33) in every
  variant tried, diagnosed as overfitting (716,025 point-rows come from
  only 4,363 independent matches - far less real signal than the row
  count suggests). The fallback logic
  (`predict_with_fallback` - degrades to Markov-only or ML-only if either
  base estimate is missing) is retained regardless. See
  [pricing/blend/README.md](../pricing/blend/README.md).
- Bounded value-detection (`trading_rules/value_detection.py`,
  `database/ingestion/tennis_data_co_uk.py`): real 2025-2026 ATP odds
  matched to 621 of our own archived matches by surname and date. Our
  best model (the blend) scores clearly worse pre-match than the
  de-vigged market (Brier 0.1984 vs 0.1828) - the honest, expected
  result; no "beat the market" claim made. Context features do
  meaningfully close the gap versus Markov alone (0.2305 → 0.1984). See
  [trading_rules/README.md](../trading_rules/README.md).

- Full API integration (`pricing/promote_model.py`, `pricing/run_promotion.py`,
  `backend/probability.py`, `backend/main.py`): a deliberately manual,
  human-run promotion script (per
  [docs/architecture/charter.md](architecture/charter.md)'s "no automatic
  model promotion") trains the EXP24 ML model on the chronologically older
  85% of matches, fits the EXP43 phase calibrator on blended predictions
  for the newer 15% (held out from the ML model's own training, so
  calibration reflects genuine out-of-sample miscalibration), and bundles
  everything - the model, calibrator, EXP33 blend weight, feature
  columns - into one versioned artefact
  (`docs/model_cards/artefacts/pricing_pipeline.joblib`, gitignored).
  `/probability` now runs the full designed pipeline end-to-end (Markov +
  ML computed independently → blend → phase calibration →
  `trading_rules.apply_trading_rules`) whenever that artefact exists -
  `model_version="blend_v1_calibrated"`, `fallback_used=false` - and
  degrades gracefully to Markov-only (`model_version="markov_v1"`,
  `fallback_used=true`) on a fresh clone before anyone has run the
  promotion script, exactly the behaviour
  [docs/architecture/logical-architecture.md](architecture/logical-architecture.md)'s
  `fallback_used` flag documents. Verified against the real archive: 4,639
  training matches, 818 held-out calibration matches, both the live and
  fallback response shapes checked directly against a running server. See
  [backend/README.md](../backend/README.md) and
  [pricing/README.md](../pricing/README.md).

- Reliability (`tests/unit/test_probability_reliability.py`,
  `tests/unit/test_feature_sync.py`, `evaluation/drift_check.py`): three
  kinds of test, matching the journey's own name in the roadmap table.
  **Failure injection** found and fixed two real gaps:
  `load_artefacts()` would have crashed the whole API at startup on a
  corrupted artefact file rather than degrading like a missing one, and
  the ML/blend/calibration path didn't distinguish "ML model failed"
  from "blend/calibration failed after a successful ML estimate" the way
  [docs/architecture/deployment.md](architecture/deployment.md)'s
  fallback table specifies - the latter case now sets
  `widen_margin=True`, which `backend/main.py` uses to price with
  `trading_rules.WIDENED_MARGIN` (0.10) instead of the default (0.05).
  **A sync test** (`build_feature_row` vs `build_point_features`) checks
  the live and offline feature-computation paths produce byte-identical
  values for the same point - a real ML reliability risk
  (train/serve skew) that would otherwise be invisible from either side
  alone. **A cross-era drift check** (EXP44) scored the promoted pipeline
  across the 2010s/2020s halves of the archive: no sharp collapse in
  either era, but a real ~11% relative Brier gap, honestly reported
  alongside the methodological confound that makes it not (yet) a clean
  drift measurement. See
  [docs/architecture/deployment.md](architecture/deployment.md#availability-and-fallback-paths)
  and [evaluation/README.md](../evaluation/README.md).

- Dashboards (`GET /ops/summary`, `frontend/src/app/ops/page.tsx`): a
  monitoring view separate from the replay/pricing dashboard, covering
  the journey's own "quality, latency, errors and regressions"
  description. Latency (median/p95) and error rates (fallback/suspended,
  by model version) come from the quote event log (Journey 7); quality
  comes from the promoted pipeline's own calibration-time evaluation
  (`PricingArtefacts.calibration_brier`/`_log_loss`/`_ece`, new fields
  computed by `pricing/promote_model.py` - see its README for why this
  needed a genuine three-way data split, not the two-way split Journey
  17 originally used, to avoid reporting the calibrator's fit to its own
  training data as if it were an honest quality number). Real numbers
  from the full archive: Brier 0.1481, log-loss 0.4648, ECE 0.0252. Not a
  live-quality metric - this system replays static historical data, so
  there's no live feed of outcomes to score served quotes against. See
  [backend/README.md](../backend/README.md) and
  [frontend/README.md](../frontend/README.md).

- Deployment (`infrastructure/`, `.github/workflows/ci.yml`,
  `pricing/registry.py`, `pricing/rollback_model.py`): containers, CI,
  monitoring and rollback, the journey's own four-word description.
  **Containers**: `Dockerfile.backend` and `Dockerfile.frontend`, plus a
  `docker-compose.yml` wiring them together - no local Docker is
  available in this project's dev environment (verified, not assumed),
  so these were written by inspection and verified for real by CI's
  `docker-build` job on GitHub's hosted runners instead, which builds
  both images and smoke-tests the backend one against `/health` - and
  that verification caught real bugs inspection alone missed: the
  backend image needed `libgomp1` installed (LightGBM's Linux wheel
  needs the OpenMP runtime, which `python:3.12-slim` doesn't ship), and
  the frontend image failed because `frontend/public/` - genuinely
  empty - was never committed to git at all (git doesn't track empty
  directories), so it didn't exist after a fresh checkout for
  `COPY --from=builder /app/public ./public` to find; fixed with a
  `.gitkeep` placeholder. Diagnosing the second one took real work with
  no local Docker and no direct CI log access (the job-logs API needs
  admin rights even on a public repo) - see
  [infrastructure/README.md](../infrastructure/README.md) for exactly
  how it was actually tracked down, including two wrong leads
  (suspecting the non-standalone build approach itself, then a broken
  diagnostic step that misreported a real failure as success) before
  the real cause surfaced.
  **CI** (`.github/workflows/ci.yml`): backend tests, frontend lint plus
  build, and the Docker build/smoke-test, on every push and PR to
  `main` - a single source of truth for the dependency list
  (`pyproject.toml`, read via `tomllib` rather than duplicated in the
  workflow). **Monitoring**: the same container health check plus
  Journey 19's `/ops/summary` dashboard. **Rollback**: a real model
  registry - every `pricing/promote_model.py` run now keeps its
  artefact under a version-stamped filename (never overwritten) and
  records itself in `docs/model_cards/artefacts/registry.json`;
  `pricing/rollback_model.py --list` / `<version>` switches which one is
  active without retraining, deliberately manual like promotion itself
  (docs/architecture/governance.md's "require review for model
  promotion" applies the same way to un-promoting). See
  [infrastructure/README.md](../infrastructure/README.md) and
  [pricing/README.md](../pricing/README.md).

- Final evaluation (`evaluation/FINAL_EVALUATION.md`,
  `docs/model_cards/blend_v1_calibrated.md`, `docs/ethics/assessment.md`):
  the journey's own "held-out test, model card, data sheet, ethics
  review," each addressed as a real document rather than a checkbox.
  **Final held-out test**: rather than inventing a new, disjoint split
  just for this journey, `FINAL_EVALUATION.md` synthesises the full
  evidence chain already gathered (EXP1 through EXP44) into one answer
  to the charter's research question - real, over the Markov baseline
  (a 15.1% Brier improvement, concentrated mostly in the ML step);
  honestly not, against the de-vigged market pre-match. **Model card**:
  training data, the exact 14-feature schema (cross-checked against
  `pricing/ml/features.py` directly, not written from memory), and the
  promoted pipeline's real quality numbers. **Data sheet**: already
  existed (`docs/data_sheets/data_provenance.md`, Journey 4) - reused,
  not duplicated. **Ethics review**: an honest self-audit against
  `docs/architecture/governance.md`'s control table that records what it
  found missing (the Markov/ML contribution split isn't exposed in
  served output; no dedicated favourite-vs-underdog/surface accuracy
  breakdown exists) alongside what's met, and states plainly that this
  project only ever ingested men's ATP data - nothing here should be
  assumed to generalise to women's tennis or other levels of play.
  README.md gains a full runnable demonstration walkthrough (ingest →
  promote → serve → both dashboards).

All 21 journeys are now complete except Journey 16 (optional
extensions), deliberately deferred as explicitly optional in the source
spec itself.

## Source

Derived from `docs/CourtEdge_Architecture_and_Task_Definition.docx`,
sections 12, 13, 15, 17, 18, 19 and 20.
