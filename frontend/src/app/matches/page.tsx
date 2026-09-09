"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { listRealMatches } from "@/lib/api";
import type { MatchSummary } from "@/lib/types";

type LoadState = "loading" | "success" | "error";

export default function MatchesPage() {
  const [state, setState] = useState<LoadState>("loading");
  const [matches, setMatches] = useState<MatchSummary[]>([]);
  const [surface, setSurface] = useState("");

  useEffect(() => {
    let cancelled = false;
    listRealMatches(surface ? { surface } : undefined)
      .then((data) => {
        if (cancelled) return;
        setMatches(data);
        setState("success");
      })
      .catch(() => {
        if (!cancelled) setState("error");
      });
    return () => {
      cancelled = true;
    };
  }, [surface]);

  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-10">
      <Link href="/" className="text-xs text-slate-500 hover:text-slate-300">
        ← Home
      </Link>

      <header className="mt-4 mb-6">
        <h1 className="text-xl font-semibold text-slate-100">Browse real matches</h1>
        <p className="mt-2 text-sm text-slate-400">
          Real, ingested match data served by the CourtEdge API, priced by
          the current placeholder estimator (the score-leader heuristic -
          the Markov and ML engines haven&apos;t been built yet).
        </p>
      </header>

      <div className="mb-4 flex items-center gap-2 text-sm">
        <label htmlFor="surface-filter" className="text-slate-400">
          Surface
        </label>
        <select
          id="surface-filter"
          value={surface}
          onChange={(e) => {
            setState("loading");
            setSurface(e.target.value);
          }}
          className="rounded-md border border-slate-700 bg-slate-900 px-2 py-1 text-slate-200"
        >
          <option value="">All</option>
          <option value="hard">Hard</option>
          <option value="clay">Clay</option>
          <option value="grass">Grass</option>
        </select>
      </div>

      {state === "loading" && <p className="text-sm text-slate-400">Loading matches…</p>}

      {state === "error" && (
        <p role="alert" className="text-sm text-red-400">
          Couldn&apos;t reach the API. Is the backend running (
          <code>python -m uvicorn backend.main:app</code>)?
        </p>
      )}

      {state === "success" && matches.length === 0 && (
        <p className="text-sm text-slate-400">No matches for this filter.</p>
      )}

      {state === "success" && matches.length > 0 && (
        <ul className="grid gap-3 sm:grid-cols-2">
          {matches.map((m) => (
            <li key={m.matchId}>
              <Link
                href={`/replay/${m.matchId}`}
                className="block rounded-lg border border-slate-800 bg-slate-900 p-4 transition hover:border-sky-700 hover:bg-slate-800/60"
              >
                <p className="text-xs uppercase tracking-wide text-slate-500">
                  {m.tournament} - {m.round}
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
      )}
    </div>
  );
}
