# frontend

The Next.js replay and pricing dashboard: match selector, point ticker,
live win-probability chart, price ticker and model-version badge.

## Status

Journey 6 (replay behaviour) is complete. There are now two data paths,
both rendered by the same `/replay/[matchId]` route and components:

- **Scenario library** (`/`) — two scripted mock matches
  (`src/lib/mockData.ts`) covering the target model scenarios: routine
  holds, break-point pressure against the favourite, a fight-back after
  dropping a set, a suspension/rain delay, and the resulting stale-quote
  data gap. Kept deliberately mock, since a completed historical match
  archive has no equivalent of a live suspension event. Probabilities here
  come from a crude placeholder heuristic tagged
  `model_version: "mock_placeholder_v0"` — never the real engine.
- **Real matches** (`/matches`) — fetched from the backend
  (`src/lib/api.ts`): `GET /matches` (with a surface filter) to browse,
  `GET /replay/{id}` plus one `POST /probability` per point to build the
  same `MatchReplay` shape the mock data uses, so no component needed to
  change. Uses `NEXT_PUBLIC_API_BASE_URL` (see `.env.example`), defaulting
  to `http://localhost:8000`.

`ReplayView` picks the path via `isScenarioLibraryMatch(matchId)`.

## Structure

- `src/lib/types.ts` — shared types mirroring the API response contract.
- `src/lib/scoring.ts` — a minimal tennis score-state machine plus the mock
  probability heuristic, used to build internally consistent scenario data.
- `src/lib/mockData.ts` — the two scripted scenario-library matches.
- `src/lib/api.ts` — the real backend client, adapting its snake_case JSON
  into the same shapes `mockData.ts` produces.
- `src/components/` — `MatchSelector`, `PointTicker`, `ProbabilityChart`,
  `PriceTicker`, `ModelVersionBadge`, `PlaybackControls`, `StatusStates`
  (loading/error), and `ReplayView` which composes them and picks the data
  source.
- `src/app/` — `/` (scenario library), `/matches` (real match browser),
  `/replay/[matchId]` (the replay view, shared by both).

## Development

```bash
npm install
cp .env.example .env.local   # only needed if the API isn't on localhost:8000
npm run dev      # http://localhost:3000 (or the next free port)
npm run lint
npm run build
```

To browse real matches, also run the backend — see
[../backend/README.md](../backend/README.md).
