# Risk register

Risks and assumptions carried by the CourtEdge architecture, with their
impact and the mitigation or evidence used to manage them. Reviewed and
updated as each journey stage closes.

| Risk / assumption | Impact | Mitigation or evidence |
|---|---|---|
| Look-ahead or leakage risk | Inflated apparent accuracy. | Match-level splits, feature versioning, explicit leakage audits. |
| Sparse data for lower-ranked or lesser-tracked players | Unreliable serve-rate estimates. | Bayesian shrinkage; fallback to tour-average prior. |
| Systematic mis-calibration at probability extremes | Overconfident quotes for heavy favourites or underdogs. | Dedicated calibration layer; phase-level calibration checks. |
| Market-odds benchmark limitations | Naive "beat the market" claims may mislead. | De-vig market odds before comparison; frame results as research, not advice. |
| Noisy crowd-sourced point annotation | Degrades model and evaluation quality. | Data-quality gates, spot checks, use only well-covered slam years. |
| Latency growth as layers are added | Slower response time. | Compute Markov and ML in parallel; cache static player context; report p95. |
| Unlicensed or paid data-source use | Legal and licensing exposure. | Use only permitted free datasets; record provenance and licence terms. |
| Ethical or responsible-gambling exposure if generalised | Potential harm if presented as betting guidance. | Explicit research framing; safer-gambling note; no staking recommendation in outputs. |
| Overfitting to a particular rule or equipment era | Looks strong on historic slams but generalises poorly. | Evaluate across multiple years and surfaces; monitor drift. |
| Complex local setup for the feature/replay store | May exceed local development constraints. | Start with a simple local Parquet store; move to a managed environment only if needed. |

## Source

Derived from `docs/CourtEdge_Architecture_and_Task_Definition.docx`, section 16.
