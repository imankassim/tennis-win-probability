# frontend

The Next.js replay and pricing dashboard: match selector, point ticker,
live win-probability chart, price ticker and model-version badge.

## Status

Journey 6 (replay behaviour) and Journey 19 (dashboards) are complete.
There are now two data paths for replay, both rendered by the same
`/replay/[matchId]` route and components, plus a separate operations
view:

- **Scenario library** (`/`) - two scripted matches (`src/lib/mockData.ts`)
  covering the target model scenarios: routine holds, break-point
  pressure against the favourite, a fight-back after dropping a set, a
  suspension/rain delay, and the resulting stale-quote data gap. The
  *point sequence* is hand-scripted, since a completed historical match
  archive has no equivalent of an on-demand live suspension event - but
  every point's probability is real model output, not a fabricated
  heuristic: `src/lib/scoring.ts` scores each scripted point through
  `POST /probability/preview` (the real Markov + ML + blend + calibration
  pipeline, scored against a hypothetical state rather than a real
  match_id). Requires the backend to be running.
- **Real matches** (`/matches`) - fetched from the backend
  (`src/lib/api.ts`): `GET /matches` (with a surface filter) to browse,
  `GET /replay/{id}` plus one `POST /probability` per point to build the
  same `MatchReplay` shape the scenario library produces, so no component
  needed to change. Uses `NEXT_PUBLIC_API_BASE_URL` (see `.env.example`),
  defaulting to `http://localhost:8000`.

`ReplayView` picks the path via `isScenarioLibraryMatch(matchId)`.

- **Operations dashboard** (`/ops`) - `GET /ops/summary`: latency
  (median/p95) and error rates (fallback/suspended) from every quote
  served since the backend's quote event log was last cleared, plus the
  promoted pipeline's own calibration-time quality snapshot (Brier,
  log-loss, ECE) if one has been promoted - `null` otherwise, rendered as
  "no promoted pipeline found." Not a live-quality metric - this system
  replays static historical data, so there's no live feed of outcomes to
  score served quotes against.

## Structure

- `src/lib/types.ts` - shared types mirroring the API response contract.
- `src/lib/scoring.ts` - a minimal tennis score-state machine that expands
  a scripted match into a point sequence, then scores every point via
  `previewProbability` (`api.ts`) - real model output for a hand-scripted
  point sequence.
- `src/lib/mockData.ts` - the two scripted scenario-library matches.
- `src/lib/api.ts` - the real backend client: `listRealMatches`,
  `getRealMatchReplay`, `getOpsSummary`, and `previewProbability` (used by
  `scoring.ts` for the scenario library, not just real matches).
- `src/components/` - `MatchSelector`, `PointTicker`, `ProbabilityChart`,
  `PriceTicker`, `ModelVersionBadge`, `PlaybackControls`, `StatusStates`
  (loading/error), and `ReplayView` which composes them and picks the data
  source.
- `src/app/` - `/` (scenario library), `/matches` (real match browser),
  `/replay/[matchId]` (the replay view, shared by both), `/ops`
  (operations dashboard).

## Development

```bash
npm install
cp .env.example .env.local   # only needed if the API isn't on localhost:8000
npm run dev      # http://localhost:3000 (or the next free port)
npm run lint
npm run build
```

The backend needs to be running for every page, including the scenario
library (`/`) - its probabilities come from `POST /probability/preview`,
not a client-side placeholder. See
[backend/README.md](../backend/README.md) for `python -m uvicorn
backend.main:app --reload`.

To browse real matches, also run the backend - see
[../backend/README.md](../backend/README.md).
