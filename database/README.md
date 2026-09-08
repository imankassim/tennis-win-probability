# database

PostgreSQL schema and ingestion for matches, players, points and outcome
labels — the transactional source of truth (see
[docs/architecture/data-architecture.md](../docs/architecture/data-architecture.md)
and
[decision 3](../docs/decisions/3-postgres-source-of-truth-duckdb-feature-store.md)).

## Status

Journey 4 (data foundation) is complete:

- `schema.sql` — the PostgreSQL DDL for `players`, `matches`, `points` and
  `outcome_labels`.
- `models.py` — plain dataclasses for the same four entities, independent
  of any database driver.
- `quality_gates.py` — the data quality gates from
  docs/architecture/data-architecture.md, as pure functions.
- `ingestion/match_charting_project.py` — parses the
  [Match Charting Project](https://github.com/JeffSackmann/tennis_MatchChartingProject)
  source CSVs (see
  [decision 9](../docs/decisions/9-match-charting-project-data-source.md)
  for why this source) into the domain models above. Malformed source rows
  are skipped and reported, not raised — one bad row shouldn't fail the
  whole ingestion run.
- `ingestion/outcomes.py` — derives the match winner and final score from
  a match's points, without parsing score notation (see the module
  docstring), quarantining matches whose chart doesn't confirm a complete
  match.
- `ingestion/run.py` — the ingestion entry point: parse, validate,
  quarantine, report. Not yet wired to a live PostgreSQL connection — see
  below.

No SQL is executed against a real PostgreSQL database yet. `run.py`
produces the same validated records a loader would insert, and has been
run against real downloaded data (see
[docs/data_sheets/data_provenance.md](../docs/data_sheets/data_provenance.md#ingestion-evidence-journey-4)
for the results) — actually writing to PostgreSQL is a small remaining
step once a target database is available, and is picked up again once the
API (Journey 5) needs to read from it.

## Running the ingestion pipeline

The source CSVs are not committed to this repository (see the data
provenance "no redistribution" rule). Download them yourself:

```bash
curl -O https://raw.githubusercontent.com/JeffSackmann/tennis_MatchChartingProject/master/charting-m-matches.csv
curl -O https://raw.githubusercontent.com/JeffSackmann/tennis_MatchChartingProject/master/charting-m-points-2020s.csv

python -m database.ingestion.run charting-m-matches.csv charting-m-points-2020s.csv
```
