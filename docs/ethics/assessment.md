# Ethics, privacy and responsible-gambling assessment

Journey 21's ethics review — an honest audit of this project against
[docs/architecture/governance.md](../architecture/governance.md)'s control
table and [docs/architecture/charter.md](../architecture/charter.md)'s
scope boundaries, checked against what's actually implemented rather than
only what was intended.

## Privacy

**Public data only.** The only data ingested is the Match Charting
Project's crowdsourced point-by-point charts (player names, match
metadata, shot sequences — all already public) and tennis-data.co.uk's
published closing odds (aggregate, bookmaker-anonymous averages). Neither
source contains real-money wagering, payment, or account data, and none
is ever collected by this system itself — see
[docs/data_sheets/data_provenance.md](../data_sheets/data_provenance.md)'s
permitted-data rules.

**No unnecessary personal data in logs.** `backend/event_log.py`'s quote
log records only match/point/model identifiers and timing (request ID,
match ID, point sequence, model version, latency, fallback/suspended) —
never a player's or viewer's identity beyond the match/player IDs already
public in the source archive. This matches FR-05
([charter.md](../architecture/charter.md)) directly.

**Gap found, not hidden**: `docs/architecture/governance.md`'s
"Explainability" control calls for exposing "the Markov versus ML
contribution split" in served output. The live `/probability` response
(`backend/schemas.py`'s `ProbabilityResponse`) returns only the final
blended, calibrated probability — not the two components separately.
`calibration_brier`/`_log_loss`/`_ece` (Journey 19) partly serve the
"retain calibration diagnostics" half of the same control, but the
contribution-split half isn't implemented. Recorded here rather than
silently left off the audit; a reasonable follow-up would add
`markov_probability`/`ml_probability` fields to the response, but that
changes a response contract other tests and the frontend depend on, so
it's noted rather than made as a late, rushed change during this
evaluation journey.

## Fairness and representation

**Men's professional tennis only.** The Match Charting Project's WTA
(women's) file was never ingested — only the men's file (`charting-m-*`,
7,532 matches). Every result in this project — the Markov baseline, the
ML model, the blend, the calibration numbers, the model card — describes
**ATP-level men's tennis specifically**. Nothing here should be assumed
to generalise to women's tennis, juniors, or any other level of play
without separate evaluation on that population's own data. This is a
scope limitation stated plainly, not a claim this system was ever
validated more broadly.

**Favourite/underdog and surface breakdowns exist but weren't the
project's main lens.** The charter's success measures call for "error
broken down by match phase ... and by context (favourite versus
underdog, surface)." Match phase breakdown is real (EXP43's phase
calibrator, `match_phase()`). Favourite-vs-underdog and surface-specific
accuracy breakdowns were not built as a dedicated report — the context
features (`surface_rate_a`/`_b`) feed the model, but no evaluation report
specifically slices Brier/ECE by surface or by favourite status. Another
honestly-recorded gap, not a claim of completeness.

## Responsible gambling and framing

**Never presented as betting advice.** No file in this codebase — API
response, dashboard copy, model card, or README — recommends a stake, a
bet, or an action. The root [README.md](../../README.md) and this
project's [prototype boundary](../../README.md#prototype-boundary)
state the research-only framing directly, and the value-detection layer
(`trading_rules/value_detection.py`) caps its reported edge
(`MAX_REPORTED_EDGE = 0.15`) specifically because "a larger disagreement
almost always signals a data problem, not a genuine mispricing" — a
deliberate design choice against ever implying a confident market-beating
signal.

**No safer-gambling signpost is currently shown**, because this
prototype has never been deployed outside a private development/portfolio
context — [docs/architecture/governance.md](../architecture/governance.md)
requires one "if ever shown outside a private portfolio context." If this
project is ever published where a wider audience might read it as
gambling-adjacent content (a public deployment, not just a source
repository or a portfolio writeup), a visible safer-gambling notice
should be added at that point, not before it's actually needed.

## Licensing and commercial-use boundary

The Match Charting Project data is licensed **CC BY-NC-SA 4.0
(non-commercial)**. This alone makes any commercial or real-money use of
this system's current data foundation a licence violation, independent
of and in addition to the responsible-gambling and regulatory concerns
already stated in the charter and governance docs. Any future real-money
adaptation would need an entirely different, commercially-licensed data
source, not just a policy decision to permit it.

## Security

Input validation exists at the API boundary (`backend/schemas.py`'s
Pydantic models; `trading_rules/rules.py` rejects out-of-bounds
probabilities before they become a served price). No secrets are
committed (`.gitignore` excludes `.env*`; no API keys or credentials
appear anywhere in this codebase, since no paid/authenticated data
source was ever integrated). CORS is deliberately wide open
(`backend/main.py`) — appropriate for a local research prototype with no
auth or session state, explicitly flagged in that file's own comment as
needing tightening before any real deployment.

## Summary

| Control (governance.md) | Status |
|---|---|
| Data provenance | Met — see data_sheets/data_provenance.md |
| Privacy | Met — public data only, minimal logging |
| Input safety | Met — Pydantic validation, trading-rules bounds checks |
| Access | Not applicable yet — single-environment prototype, no deployed multi-tenant access to separate |
| Secrets | Met — none committed, none needed |
| Auditability | Met — request ID, model version, latency, fallback all logged (Journey 7) |
| Explainability | **Partially met** — calibration diagnostics retained; Markov/ML contribution split not exposed in served output (gap recorded above) |
| Human review | Met — model promotion and rollback are both deliberately manual (Journeys 17, 20) |
| Responsible framing | Met — no betting-advice framing anywhere; safer-gambling signpost deferred until public deployment, per governance.md's own conditional wording |
| Release approval | Met by scope — no real deployment against a live feed exists or is planned |

This is an honest self-assessment, not an external audit — it should not
be read as a substitute for real legal, regulatory or responsible-gambling
review before any use beyond this project's stated research/portfolio
scope (see the [Prototype boundary](../../README.md#prototype-boundary)).
