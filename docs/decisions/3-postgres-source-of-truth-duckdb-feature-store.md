# 3. PostgreSQL as source of truth, DuckDB/Parquet as feature-and-replay store

- Status: Accepted
- Date: 2026-09-08

## Context

The data architecture needs one authoritative, transactionally consistent
record of matches, players, points and outcome labels, and a separate path
for fast, point-in-time feature computation and match replay (a different
access pattern: sequential, columnar, read-heavy, rebuildable). Conflating
these into one store either slows down transactional writes or slows down
replay-scale analytical reads.

## Decision

Use PostgreSQL as the transactional source of truth. Use DuckDB or Parquet
files as a separate, rebuildable feature-and-replay store, derived from
PostgreSQL rather than authoritative on its own.

## Consequences

- Matches the storage-responsibility split in the data architecture: the
  feature store is "not responsible for being the authoritative record",
  and PostgreSQL is "not responsible for fast point-in-time feature
  replay".
- A feature-store failure degrades to "minimal state-only Markov
  calculation" (deployment architecture fallback table) rather than losing
  data, because PostgreSQL remains intact.
- Requires a rebuild pipeline (PostgreSQL → feature store) whose logic must
  be versioned identically for training and serving, per the offline
  training controls (no train/serve skew in feature generation).
- No local Postgres/DuckDB server is assumed to be running in every
  development environment; local setup is documented in
  [database/README.md](../../database/README.md) as it is built out in
  journey 4.
