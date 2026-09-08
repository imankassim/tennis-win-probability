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
- `ingestion/tennis_data_co_uk.py` — parses tennis-data.co.uk's yearly
  odds files and matches them to our own archive by player surname and
  date proximity (no shared match_id between the two sources). Evaluation
  benchmark only — see
  [trading_rules/README.md](../trading_rules/README.md) for the Journey
  15 value-detection backtest this feeds.
- `ingestion/run.py` — the ingestion entry point: parse, validate,
  quarantine, report. Accepts multiple points files (e.g. one per decade)
  and merges them. Not yet wired to a live PostgreSQL connection — see
  below.

No SQL is executed against a real PostgreSQL database yet. `run.py`
produces the same validated records a loader would insert — actually
writing to PostgreSQL is a small remaining step once a target database is
available, and is picked up again once it's needed for real serving.

## Running the ingestion pipeline

The source CSVs are not committed to this repository (see the data
provenance "no redistribution" rule). Download them yourself:

```bash
curl -O https://raw.githubusercontent.com/JeffSackmann/tennis_MatchChartingProject/master/charting-m-matches.csv
curl -O https://raw.githubusercontent.com/JeffSackmann/tennis_MatchChartingProject/master/charting-m-points-2010s.csv
curl -O https://raw.githubusercontent.com/JeffSackmann/tennis_MatchChartingProject/master/charting-m-points-2020s.csv

python -m database.ingestion.run charting-m-matches.csv charting-m-points-2010s.csv charting-m-points-2020s.csv
```

## Ingestion evidence

Run against the full 2010s and 2020s Match Charting Project points files
(904,513 points across 5,568 matches with points loaded):

- 5,453 matches produced a confirmed, complete outcome label.
- 115 matches were correctly quarantined as incomplete charts (the chart
  stops before a set or the match is actually won) rather than given a
  guessed outcome.
- 36 match-level violations (malformed source rows, e.g. an unescaped
  comma shifting every later column) were skipped and reported rather
  than crashing the run.

See [evaluation/README.md](../evaluation/README.md) and
[pricing/markov/README.md](../pricing/markov/README.md) for what this
data was then used to evaluate (EXP1 vs EXP2 vs the Markov baseline).
