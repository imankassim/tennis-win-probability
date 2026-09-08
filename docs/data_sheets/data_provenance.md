# Data provenance and permitted-data rules

CourtEdge uses only public data sources with confirmed, recorded usage
rights. This document is the provenance register referenced by the data
quality gates and by the governance architecture.

## Approved sources

| Source | Content | Licence / terms | Use in CourtEdge |
|---|---|---|---|
| Jeff Sackmann, [`tennis_MatchChartingProject`](https://github.com/JeffSackmann/tennis_MatchChartingProject) GitHub repository | Crowdsourced, shot-by-shot point-by-point data and match metadata for charted ATP/WTA matches | CC BY-NC-SA 4.0 (non-commercial), stated in the repo's README | Primary source for matches, players, points and outcome labels. See [decision 9](../decisions/9-match-charting-project-data-source.md) for why this replaced `tennis_slam_pointbypoint`. |
| ATP/WTA rankings | Player ranking history | Not yet sourced | Still deferred — Journey 7 built recent-form, surface-record and head-to-head context features entirely from our own ingested match archive (no external source needed for those). Only `current_rank`/`rank_points` remain unpopulated; sourced when the ML feature set (Journey 10-11) actually needs them. |
| [tennis-data.co.uk](http://tennis-data.co.uk/alldata.php) | Historical ATP/WTA match results and closing odds (yearly `.xlsx` files, one per tour) | Published for personal / non-commercial research use | Evaluation benchmark only — for de-vigged comparison and the bounded, research-only value-detection layer (Journey 15). Never used as an input feature and never treated as ground truth. Uses the `AvgW`/`AvgL` columns (the average closing odds across bookmakers), not any single bookmaker's price. |

### A note on the originally-named sources

The architecture document originally named `tennis_atp`, `tennis_wta` and
`tennis_slam_pointbypoint` (also Sackmann's) as the primary sources. While
starting Journey 4, all three had been removed from GitHub (confirmed via
the GitHub API returning 404). The Wayback Machine shows `tennis_atp` was
still present as of March 2026, and that its README did state the CC
BY-NC-SA 4.0 licence this document already claimed — so the provenance
claim for that data was accurate for as long as it was reachable, but it
is no longer available as a live source. See
[decision 9](../decisions/9-match-charting-project-data-source.md) for the
full reasoning behind switching to the Match Charting Project instead.

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
   the Match Charting Project / Tennis Abstract and tennis-data.co.uk per
   their terms.

## Ingestion evidence (Journey 4)

The ingestion pipeline (`database/ingestion/`) has been run against real
Match Charting Project data — the men's matches file in full (7,532
matches) and the full 2010s and 2020s points files (904,513 points across
5,568 matches), downloaded fresh rather than committed, per rule 4 above.
Result:

- 5,453 matches produced a confirmed, complete outcome label.
- 115 matches were correctly quarantined as incomplete charts (the chart
  stops before a set or the match is actually won) rather than given a
  guessed outcome.
- 36 source rows failed to parse (a handful of matches-file rows have an
  unescaped comma shifting every later column) and were skipped and
  reported rather than crashing the run.

An initial pass against a smaller, bounded sample (~28,800 points across
190 matches) is what this ingestion is scaled up from — see
[evaluation/README.md](../../evaluation/README.md) for what that scale-up
changed about the Markov-vs-heuristic evaluation result.

Run it yourself: download the CSVs from the Match Charting Project, then
`python -m database.ingestion.run <matches.csv> <points1.csv> [<points2.csv> ...]`.

## Source

Derived from `docs/CourtEdge_Architecture_and_Task_Definition.docx`,
sections 8.3, 11 and 21.
