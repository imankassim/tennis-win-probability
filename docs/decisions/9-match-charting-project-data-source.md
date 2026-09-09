# 9. Source point-by-point data from the Match Charting Project, not tennis_slam_pointbypoint

- Status: Accepted
- Date: 2026-09-08

## Context

[Decision 8](8-public-non-commercial-data-only.md) restricted CourtEdge to
public, non-commercial-licensed data, naming Jeff Sackmann's
`tennis_atp` / `tennis_wta` / `tennis_slam_pointbypoint` GitHub
repositories as the source. While starting Journey 4 (data foundation),
all three repositories turned out to have been removed from GitHub -
confirmed via the GitHub API (404) and cross-checked against the Wayback
Machine, which shows `tennis_atp` still present in March 2026 and
confirms it was genuinely licensed CC BY-NC-SA 4.0, matching what
[docs/data_sheets/data_provenance.md](../data_sheets/data_provenance.md)
already claimed.

Old forks of the removed repositories exist (data through roughly 2015),
and a community-maintained continuation for match results exists
(TML-Database) but scrapes ATP.com directly under unclear licence terms
that don't meet decision 8's bar. Sackmann's other repository, the
[Match Charting Project](https://github.com/JeffSackmann/tennis_MatchChartingProject),
is still live and actively updated, carries the same CC BY-NC-SA 4.0
licence, and provides genuinely point-by-point (in fact shot-by-shot)
data - a superset of what `tennis_slam_pointbypoint` offered. This choice
was put to the user directly, given it affects data provenance and
licensing framing; the Match Charting Project was their preference.

## Decision

Source match and point data from the Match Charting Project
(`charting-*-matches.csv`, `charting-*-points-*.csv`) instead of
`tennis_slam_pointbypoint`. Player/ranking data (originally from
`tennis_atp`/`tennis_wta`) is deferred until Journey 7 (context features)
needs it - the Match Charting Project's matches files alone are sufficient
for the Match/Player/Point/OutcomeLabel schema Journey 4 needs.

## Consequences

- Coverage is crowdsourced (charted by volunteers) rather than a complete
  archive of every Grand Slam match - fewer matches, but richer per-match
  detail (shot-level codes), which opens a direct path to `EXP50`
  (shot-level features) later using the same source instead of a separate
  one.
- The ingestion parser (`database/ingestion/match_charting_project.py`)
  targets this format specifically. If a future decision reintroduces
  `tennis_slam_pointbypoint`-shaped data (e.g. a maintained mirror
  appears), it needs its own parser - the domain models in
  `database/models.py` and the quality gates are already source-agnostic.
- Not every charted match is complete (some charts stop mid-match).
  `database/ingestion/outcomes.py` detects this from the data itself
  (whether the final recorded point actually completes a set and the
  match) and quarantines incomplete matches rather than guessing an
  outcome - see the real evidence in
  [docs/data_sheets/data_provenance.md](../data_sheets/data_provenance.md).
- `docs/data_sheets/data_provenance.md` and decision 8's source list are
  updated to reflect this; decision 8's underlying principle (public,
  non-commercial-licensed data only, market odds as an evaluation
  benchmark only) is unchanged.
