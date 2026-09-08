# backend

FastAPI application layer: `/health`, `GET /matches`,
`GET /replay/{match_id}`, `POST /probability`.

## Status

Journeys 5-10 (API, replay behaviour, instrumentation, evaluation, Markov
baseline, context features) are complete. `context_features.py` was built
ahead of schedule by mistake, between Journeys 6 and 7 — the module
itself was always correct and tested, just out of sequence; `player_rating.py`
finishes Journey 10's remaining scope (ranking) with a self-computed Elo
rating, since no external ranking feed was ever sourced.

`/probability` runs the full designed pipeline (Journey 17): Markov and
ML estimates computed independently, blended at the promoted weight,
phase-calibrated — `model_version="blend_v1_calibrated"` — whenever a
promoted pipeline exists (`pricing/promote_model.py`, see
[pricing/README.md](../pricing/README.md)), degrading gracefully to the
Markov engine alone (`model_version="markov_v1"`, `fallback_used=true`)
if none has been promoted yet. A real match-state parser
(`match_state.py`) provides break-point detection and within-game score,
both reconstructed from the already-stored raw points, no new fields
needed. The response contract matches
[docs/architecture/logical-architecture.md](../docs/architecture/logical-architecture.md)'s
example response exactly. CORS is wide open for now (research prototype,
no auth) — tighten before any real deployment.

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
- `context_features.py` — the player context service: recent form,
  surface record and head-to-head, computed from our own match archive
  with a strict no-look-ahead cutoff. Its first consumer was the ML
  feature set (`pricing/ml/features.py`'s `compute_match_context_features`,
  a bulk one-pass variant of the same idea); `main.py` builds that same
  bulk cache at startup for live `/probability` requests, so a served
  request scores the identical feature the model was trained on.
- `player_rating.py` — a self-computed Elo rating (finishing Journey 10):
  no external ATP/WTA rankings feed was ever sourced, so this computes a
  standard Elo rating directly from our own match archive instead — same
  no-look-ahead discipline. Verified sensible against real data: top
  rated players are Sinner, Alcaraz, Djokovic, Federer, in that order.
- `event_log.py` — Journey 7 (instrumentation): logs one JSONL record per
  served quote (request ID, model version, latency, fallback/suspended)
  to `data/quote_log.jsonl` by default, or `COURTEDGE_QUOTE_LOG_PATH`.
  Journey 8's evaluation harness reads this file.
- `probability.py` — orchestrates the full pipeline (Journey 17): Markov
  and ML estimates, blend, phase calibration, if a promoted pipeline
  exists (`pricing/promote_model.py`); Markov alone otherwise. Margin,
  price bounds and suspension are `trading_rules/rules.py`'s job, applied
  in `main.py` after this module returns its raw probability.
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
