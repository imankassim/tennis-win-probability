import type { ProbabilityQuote } from "@/lib/types";

export function ModelVersionBadge({ quote }: { quote: ProbabilityQuote }) {
  return (
    <div className="flex flex-wrap items-center gap-2 text-xs">
      <span className="rounded-full bg-slate-800 px-2.5 py-1 font-mono text-slate-200">
        {quote.modelVersion}
      </span>
      {quote.fallbackUsed && (
        <span className="rounded-full bg-amber-900/60 px-2.5 py-1 text-amber-200">
          fallback used
        </span>
      )}
      {quote.stale && (
        <span className="rounded-full bg-amber-900/60 px-2.5 py-1 text-amber-200">stale</span>
      )}
      {quote.suspended && (
        <span className="rounded-full bg-red-900/60 px-2.5 py-1 text-red-200">suspended</span>
      )}
      <span className="font-mono text-slate-500">{quote.probabilityRequestId}</span>
    </div>
  );
}
