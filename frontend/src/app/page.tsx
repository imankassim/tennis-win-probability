import Link from "next/link";
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
          Research prototype only - not betting advice, not a staking
          recommendation.
        </p>
      </header>

      <div className="mb-8 flex items-center justify-between">
        <h2 className="text-sm font-medium text-slate-300">Scenario library</h2>
        <div className="flex gap-4">
          <Link href="/matches" className="text-xs text-sky-400 hover:text-sky-300">
            Browse real matches →
          </Link>
          <Link href="/ops" className="text-xs text-sky-400 hover:text-sky-300">
            Ops dashboard →
          </Link>
        </div>
      </div>
      <MatchSelector matches={matches} />
    </div>
  );
}
