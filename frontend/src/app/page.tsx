import { MatchSelector } from "@/components/MatchSelector";
import { listMatches } from "@/lib/mockData";

export default function HomePage() {
  const matches = listMatches();

  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-10">
      <header className="mb-8">
        <h1 className="text-2xl font-semibold text-slate-100">CourtEdge</h1>
        <p className="mt-2 text-sm text-slate-400">
          An in-play tennis probability and pricing research prototype. Select
          a match to replay it point by point and inspect the returned
          probability and price.
        </p>
        <p className="mt-2 text-xs text-slate-600">
          Research prototype only — not betting advice, not a staking
          recommendation.
        </p>
      </header>
      <MatchSelector matches={matches} />
    </div>
  );
}
