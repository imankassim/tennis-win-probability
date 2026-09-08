# Deployment architecture

For a local learning build, services may run through local processes or
containers. For a cloud build, the same logical roles can be deployed using
approved managed services. The following describes roles, not a mandatory
vendor-specific configuration.

| Layer | Local / development role | Cloud-oriented role |
|---|---|---|
| Web | Next.js development server. | Static or server-rendered web hosting. |
| API | FastAPI process. | Container or managed application runtime. |
| Operational data | Local PostgreSQL. | Managed relational database. |
| Feature and replay store | Local DuckDB or Parquet files. | Managed analytical store or object storage. |
| Events / analytics | PostgreSQL, Parquet or notebook inputs. | Message ingestion plus analytical warehouse. |
| Training | Local or managed notebook for reproducible experiments. | Managed ML jobs and registry where approved. |
| Secrets | Local environment file excluded from source control. | Managed secret store. |
| Monitoring | Application logs and local metrics. | Central logs, metrics, alerts and dashboards. |

## Availability and fallback paths

| Failure | Expected behaviour | Verified |
|---|---|---|
| ML model unavailable | Serve the Markov-only probability and mark `ml_fallback` as true. | Yes — `backend/probability.py`'s `fallback_used` field (this project's actual name for `ml_fallback`) is `true` both when no promoted artefact exists at all and when a present artefact's ML model raises at request time. |
| Blend or calibration service unavailable | Serve the raw Markov probability with a widened margin. | Yes — distinguished from plain ML failure: a blend/calibration failure that occurs *after* a successful ML estimate sets `widen_margin=True`, which `backend/main.py` uses to price with `trading_rules.WIDENED_MARGIN` (0.10) instead of the default (0.05). |
| Feature or replay store unavailable | Use a minimal state-only Markov calculation. | Partially — the Markov engine only ever needs score-state and serve rates (no context/replay store dependency to fail), so this row is naturally satisfied by the architecture rather than by a specific test. |
| Trading-rules service failure | Suspend pricing entirely rather than guess a margin. | Yes — `trading_rules/rules.py` was already covered by Journey 13 (`tests/unit/test_trading_rules.py`): missing, invalid, or unpriceable probabilities all suspend rather than serve a guessed price. |
| Point-feed lag or stale data | Mark the quote as stale and stop advancing the displayed price. | `is_stale()` is implemented and tested, not yet meaningful in this environment (this system replays static historical data, not a live feed — see "what will not be built" in charter.md). |
| Outcome-label pipeline failure | Exclude the affected match from the current evaluation run rather than include unreliable ground truth. | Yes — `database/ingestion/outcomes.py`'s `derive_outcome` quarantines a match rather than guessing its outcome; quarantined matches are excluded from every evaluation harness (Journey 8) and from training (Journey 11+). |

Failure-injection tests for the two rows this journey (18) added coverage
for: `tests/unit/test_probability_reliability.py` (ML model raising,
blend/calibration raising, a corrupted artefact file, a missing artefact
file — each checked against the model_version, fallback_used and
widen_margin the row above promises). A sync test
(`tests/unit/test_feature_sync.py`) additionally guards against
training/serving feature skew — a failure mode this table doesn't name
directly, since it produces silently wrong numbers rather than a
detectable failure, but one the same "must not surprise the caller"
spirit applies to. A cross-era drift check
(`evaluation/drift_check.py`, EXP44) covers the risk register's
"overfitting to a particular rule or equipment era" concern — see
[experiments/EXP44-cross-era-drift.md](../../experiments/EXP44-cross-era-drift.md)
for the real result.

## Source

Derived from `docs/CourtEdge_Architecture_and_Task_Definition.docx`, section 10.
