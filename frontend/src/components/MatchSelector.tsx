import Link from "next/link";
import type { MatchSummary } from "@/lib/types";

export function MatchSelector({ matches }: { matches: MatchSummary[] }) {
  return (
    <ul className="grid gap-3 sm:grid-cols-2">
      {matches.map((m) => (
        <li key={m.matchId}>
          <Link
            href={`/replay/${m.matchId}`}
            className="block rounded-lg border border-slate-800 bg-slate-900 p-4 transition hover:border-sky-700 hover:bg-slate-800/60"
          >
            <p className="text-xs uppercase tracking-wide text-slate-500">
              {m.tournament} — {m.round}
            </p>
            <p className="mt-1 text-lg font-medium text-slate-100">
              {m.playerA} <span className="text-slate-500">vs</span> {m.playerB}
            </p>
            <p className="mt-1 text-xs text-slate-500">
              {m.surface} · best of {m.bestOf} · {m.date}
            </p>
          </Link>
        </li>
      ))}
    </ul>
  );
}
