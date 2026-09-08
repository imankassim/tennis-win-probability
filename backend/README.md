# backend

FastAPI application layer: `/health`, `GET /matches`,
`GET /replay/{match_id}`, `POST /probability`.

## Status

Journey 6 (replay behaviour) is complete, on top of Journey 5's API. Uses
the score-leader heuristic (EXP2) as a stand-in estimator until the Markov
chain (Journey 9) exists, and a real match-state parser
(`match_state.py`) for break-point detection — reconstructed from the
already-stored raw points, no new fields needed. The response contract
matches
[docs/architecture/logical-architecture.md](../docs/architecture/logical-architecture.md)'s
example response, so swapping in the real estimator later shouldn't
change the API shape. CORS is wide open for now (research prototype, no
auth) — tighten before any real deployment.

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
- `probability.py` — computes a probability/price from the score-leader
  heuristic; the placeholder margin and lack of trading rules are
  documented in the module.
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
