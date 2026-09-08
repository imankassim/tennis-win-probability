# Data provenance and permitted-data rules

CourtEdge uses only public data sources with confirmed, recorded usage
rights. This document is the provenance register referenced by the data
quality gates and by the governance architecture.

## Approved sources

| Source | Content | Licence / terms | Use in CourtEdge |
|---|---|---|---|
| Jeff Sackmann, `tennis_slam_pointbypoint` / `tennis_atp` / `tennis_wta` GitHub repositories | Point-by-point sequences, match results, player and ranking data | CC BY-NC-SA (non-commercial) | Primary source for matches, players, points and outcome labels. |
| ATP/WTA rankings and results (via the Sackmann repositories) | Player ranking history, results | CC BY-NC-SA (non-commercial) | Player-context features: ranking, recent form. |
| tennis-data.co.uk | Historical match odds | Published for personal / non-commercial research use | Evaluation benchmark only — for de-vigged comparison and the bounded, research-only value-detection layer. Never used as an input feature and never treated as ground truth. |

## Permitted-data rules

1. **Non-commercial, public data only.** No paid or restricted-licence feed
   is ingested without confirmed usage rights recorded here first.
2. **Provenance before ingestion.** Every dataset entering the catalogue
   must have its source, licence terms and any restriction recorded in this
   file before it is loaded.
3. **Market odds are a benchmark, not ground truth.** tennis-data.co.uk odds
   are used exclusively for offline evaluation and the bounded
   value-detection layer, and are de-vigged before any comparison. They are
   never used as a serving-time feature.
4. **No redistribution of licensed data.** Raw third-party data files are not
   committed to this repository; only ingestion code, schemas and derived,
   non-identifying aggregates are. See `.gitignore` for the raw-data
   exclusion.
5. **No real user or wagering data.** CourtEdge never collects real-money
   wagering, payment or account data. Any dashboard interaction logging is
   anonymous and exists only when it has a defined evaluation purpose.
6. **Quarantine on failure.** A data-quality failure quarantines the
   affected match rather than corrupting the wider dataset (see the data
   quality gates in [docs/architecture/data-architecture.md](../architecture/data-architecture.md)).
7. **Attribution.** Any published output derived from these sources credits
   Sackmann's repositories and tennis-data.co.uk per their terms.

## Source

Derived from `docs/CourtEdge_Architecture_and_Task_Definition.docx`,
sections 8.3, 11 and 21.
