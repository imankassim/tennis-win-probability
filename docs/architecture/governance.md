# Security, privacy and governance architecture

| Control area | CourtEdge design response |
|---|---|
| Data provenance | Record the Sackmann and tennis-data.co.uk source, licence terms and any non-commercial restriction (see [docs/data_sheets/data_provenance.md](../data_sheets/data_provenance.md)). |
| Privacy | Use only public match and player data. No real user wagering or financial data. Any dashboard analytics are anonymous and purposeful. |
| Input safety | Validate match state, point sequence and score-format inputs. |
| Access | Separate development, deployment and data privileges according to the chosen environment. |
| Secrets | Never commit passwords, tokens or connection strings, including any key for a paid odds feed. |
| Auditability | Version Markov parameters, features, the ML model, the calibration map and the trading-rule configuration. |
| Explainability | Expose the Markov versus ML contribution split and retain calibration diagnostics for investigation. |
| Human review | Require review for model promotion, governance decisions and any change to trading rules. |
| Responsible framing | The prototype is a research and educational tool. It must not be presented as betting advice, must not encourage wagering, and should carry a safer-gambling signpost if ever shown outside a private portfolio context. |
| Release approval | Any real deployment against a live feed would separately require that provider's licence terms and full legal, regulatory and responsible-gambling review; this is explicitly out of scope here. |

## Prototype boundary

This architecture document is a technical learning and portfolio design. It
does not constitute a compliant real-money betting system, and no part of it
should be deployed against real markets or real customers without full
legal, regulatory and responsible-gambling review.

## Source

Derived from `docs/CourtEdge_Architecture_and_Task_Definition.docx`, section 11.
