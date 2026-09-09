"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getOpsSummary } from "@/lib/api";
import type { OpsSummary, PageState } from "@/lib/types";

function StatCard({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900 p-4">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-slate-100">{value}</p>
      {hint && <p className="mt-1 text-xs text-slate-500">{hint}</p>}
    </div>
  );
}

function formatPct(rate: number): string {
  return `${(rate * 100).toFixed(1)}%`;
}

function formatMs(ms: number | null): string {
  return ms === null ? "—" : `${ms.toFixed(1)} ms`;
}

export default function OpsPage() {
  const [state, setState] = useState<PageState>("loading");
  const [summary, setSummary] = useState<OpsSummary | null>(null);

  useEffect(() => {
    let cancelled = false;
    getOpsSummary()
      .then((data) => {
        if (cancelled) return;
        setSummary(data);
        setState("success");
      })
      .catch(() => {
        if (!cancelled) setState("error");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-10">
      <Link href="/" className="text-xs text-slate-500 hover:text-slate-300">
        ← Home
      </Link>

      <header className="mt-4 mb-6">
        <h1 className="text-xl font-semibold text-slate-100">Operations dashboard</h1>
        <p className="mt-2 text-sm text-slate-400">
          Quality, latency and error rates for the served pricing pipeline
          (Journey 19) - quality is the promoted model&apos;s own
          calibration-time evaluation, not a live metric, since this
          system replays static historical data rather than a live feed.
        </p>
      </header>

      {state === "loading" && <p className="text-sm text-slate-400">Loading…</p>}

      {state === "error" && (
        <p role="alert" className="text-sm text-red-400">
          Couldn&apos;t reach the API. Is the backend running (
          <code>python -m uvicorn backend.main:app</code>)?
        </p>
      )}

      {state === "success" && summary && (
        <div className="space-y-8">
          <section>
            <h2 className="mb-3 text-sm font-medium text-slate-300">Latency</h2>
            <div className="grid gap-3 sm:grid-cols-3">
              <StatCard label="Quotes served" value={String(summary.latency.nQuotes)} />
              <StatCard label="Median latency" value={formatMs(summary.latency.medianMs)} />
              <StatCard label="p95 latency" value={formatMs(summary.latency.p95Ms)} />
            </div>
          </section>

          <section>
            <h2 className="mb-3 text-sm font-medium text-slate-300">Errors and fallbacks</h2>
            <div className="grid gap-3 sm:grid-cols-2">
              <StatCard
                label="Fallback rate"
                value={formatPct(summary.errors.fallbackRate)}
                hint={`${summary.errors.fallbackCount} of ${summary.latency.nQuotes} quotes`}
              />
              <StatCard
                label="Suspended rate"
                value={formatPct(summary.errors.suspendedRate)}
                hint={`${summary.errors.suspendedCount} of ${summary.latency.nQuotes} quotes`}
              />
            </div>
            {Object.keys(summary.errors.modelVersionCounts).length > 0 && (
              <div className="mt-3 rounded-lg border border-slate-800 bg-slate-900 p-4">
                <p className="text-xs uppercase tracking-wide text-slate-500">
                  Model version breakdown
                </p>
                <ul className="mt-2 space-y-1 text-sm text-slate-300">
                  {Object.entries(summary.errors.modelVersionCounts).map(([version, count]) => (
                    <li key={version} className="flex justify-between">
                      <span>{version}</span>
                      <span className="text-slate-500">{count}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </section>

          <section>
            <h2 className="mb-3 text-sm font-medium text-slate-300">Promoted model quality</h2>
            {summary.model === null ? (
              <p className="text-sm text-slate-400">
                No promoted pipeline found - serving Markov-only. Run{" "}
                <code>python -m pricing.run_promotion</code> to promote one.
              </p>
            ) : (
              <div className="grid gap-3 sm:grid-cols-3">
                <StatCard label="Model version" value={summary.model.modelVersion} />
                <StatCard
                  label="Calibration Brier"
                  value={summary.model.calibrationBrier.toFixed(4)}
                  hint="lower is better"
                />
                <StatCard
                  label="Calibration ECE"
                  value={summary.model.calibrationEce.toFixed(4)}
                  hint="lower is better"
                />
                <StatCard
                  label="Training matches"
                  value={String(summary.model.nTrainingMatches)}
                />
                <StatCard
                  label="Calibration matches"
                  value={String(summary.model.nCalibrationMatches)}
                />
                <StatCard
                  label="Trained at"
                  value={new Date(summary.model.trainedAt).toLocaleString()}
                />
              </div>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
