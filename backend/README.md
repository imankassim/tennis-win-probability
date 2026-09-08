# backend

FastAPI application layer: `/health`, `/replay/{match_id}`,
`POST /probability`.

## Status

Journey 5 (API) is complete: a full dashboard-to-Python path exists, using
the score-leader heuristic (EXP2) as a stand-in estimator until the Markov
chain (Journey 9) exists. The response contract already matches
[docs/architecture/logical-architecture.md](../docs/architecture/logical-architecture.md)'s
example response, so swapping in the real estimator later shouldn't change
the API shape.

The frontend still runs on its own local mock data
(`frontend/src/lib/mockData.ts`) — wiring it to this API is Journey 6
(replay behaviour).

## Structure

- `repository.py` — a `MatchRepository` protocol plus an in-memory
  implementation, loadable from the demo fixture or from real ingested
  data.
- `fixtures.py` — a small synthetic demo match (`demo_backend_001`), used
  by default so the app runs without needing real downloaded data.
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
