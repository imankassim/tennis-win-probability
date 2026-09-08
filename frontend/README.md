# frontend

The Next.js replay and pricing dashboard: match selector, point ticker,
live win-probability chart, price ticker and model-version badge.

## Status

Journey 2 (first visible dashboard) is complete: a static replay dashboard
running entirely on scripted mock data (`src/lib/mockData.ts`), with all
four target page states reachable (loading, success, error, and a
suspended quote within a successful replay). No backend exists yet — that's
Journey 5. Swapping the mock data source for real `/replay` and
`/probability` calls should not require reshaping the components, since
`src/lib/types.ts` mirrors the API response contract in
[docs/architecture/logical-architecture.md](../docs/architecture/logical-architecture.md).

The probability curve in the mock data comes from a deliberately crude
placeholder heuristic (`mockPlaceholderProbability` in `src/lib/scoring.ts`),
never the real Markov/ML engine — every mock quote is tagged
`model_version: "mock_placeholder_v0"` so it can never be mistaken for one.

## Structure

- `src/lib/types.ts` — shared types mirroring the API response contract.
- `src/lib/scoring.ts` — a minimal tennis score-state machine plus the mock
  probability heuristic, used to build internally consistent replay data.
- `src/lib/mockData.ts` — two scripted demo matches covering the target
  model scenarios (routine holds, break-point pressure against the
  favourite, a fight-back after dropping a set, a suspension/rain delay,
  and the resulting stale-quote data gap).
- `src/components/` — `MatchSelector`, `PointTicker`, `ProbabilityChart`,
  `PriceTicker`, `ModelVersionBadge`, `PlaybackControls`, `StatusStates`
  (loading/error), and `ReplayView` which composes them.
- `src/app/` — `/` (match selector) and `/replay/[matchId]` (the replay
  view).

## Development

```bash
npm install
npm run dev      # http://localhost:3000 (or the next free port)
npm run lint
npm run build
```
