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

| Failure | Expected behaviour |
|---|---|
| ML model unavailable | Serve the Markov-only probability and mark `ml_fallback` as true. |
| Blend or calibration service unavailable | Serve the raw Markov probability with a widened margin. |
| Feature or replay store unavailable | Use a minimal state-only Markov calculation. |
| Trading-rules service failure | Suspend pricing entirely rather than guess a margin. |
| Point-feed lag or stale data | Mark the quote as stale and stop advancing the displayed price. |
| Outcome-label pipeline failure | Exclude the affected match from the current evaluation run rather than include unreliable ground truth. |

## Source

Derived from `docs/CourtEdge_Architecture_and_Task_Definition.docx`, section 10.
