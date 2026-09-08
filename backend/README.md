# backend

FastAPI application layer: `/health`, `GET /matches`,
`GET /replay/{match_id}`, `POST /probability`.

## Status

Journeys 5-9 (API, replay behaviour, instrumentation, evaluation, Markov
baseline) are complete. `context_features.py` is Journey 10 content,
built ahead of schedule by mistake — the module itself is correct and
tested, but its remaining scope (ranking) is picked up properly when
Journey 10 resumes.

`/probability` now uses the Markov engine (`pricing/markov/`, model
version `markov_v1`) as its estimator, replacing the score-leader
heuristic placeholder from Journey 5. A real match-state parser
(`match_state.py`) provides break-point detection and within-game score,
both reconstructed from the already-stored raw points, no new fields
needed. The response contract matches
[docs/architecture/logical-architecture.md](../docs/architecture/logical-architecture.md)'s
example response, so swapping the estimator again (ML, Journey 11)
shouldn't change the API shape. CORS is wide open for now (research
prototype, no auth) — tighten before any real deployment.

The frontend (`frontend/src/lib/api.ts`) is wired to this API for real
match browsing and replay; its own scripted scenario-library matches stay
separate, since they demonstrate page states (suspension) a completed
match archive has no equivalent of.

## Structure

- `repository.py` — a `MatchRepository` protocol plus an in-memory
  implementation, loadable from the demo fixture or from real ingested
  data. `list_matches()` only returns matches that actually have points.
- `fixtures.py` — a small synthetic demo match (`demo_backend_001`), used
  by default so the app runs without needing real downloaded data.
- `match_state.py` — the match-state parser: derives whether a point is a
  break point from the earlier points in the same game.
- `context_features.py` — the player context service (Journey 10, built
  early): recent form, surface record and head-to-head, computed from our
  own match archive with a strict no-look-ahead cutoff. Not yet wired
  into an endpoint — its first consumer will be the ML feature set
  (Journey 11).
- `event_log.py` — Journey 7 (instrumentation): logs one JSONL record per
  served quote (request ID, model version, latency, fallback/suspended)
  to `data/quote_log.jsonl` by default, or `COURTEDGE_QUOTE_LOG_PATH`.
  Journey 8's evaluation harness reads this file.
- `probability.py` — computes a probability/price using the Markov engine
  (`pricing/markov/`); the placeholder margin and lack of trading rules
  are documented in the module. Serve rates are estimated per match and
  cached (they don't change point to point) in `main.py`.
- `schemas.py` — the Pydantic request/response models.
- `main.py` — the FastAPI app and routes.

## Running it

```bash
python -m uvicorn backend.main:app --reload
```

To serve real ingested data instead of the demo fixture, point
`COURTEDGE_DATA_DIR` at a directory containing a `charting-*-matches.csv`
and a `charting-*-points-*.csv` (see
[database/README.md](../database/README.md) for how to get them):

```bash
COURTEDGE_DATA_DIR=/path/to/csvs python -m uvicorn backend.main:app --reload
```
