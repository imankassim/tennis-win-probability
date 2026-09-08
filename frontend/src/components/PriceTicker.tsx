import type { MatchSummary, ProbabilityQuote } from "@/lib/types";

export function PriceTicker({
  quote,
  match,
}: {
  quote: ProbabilityQuote;
  match: MatchSummary;
}) {
  if (quote.suspended) {
    return (
      <div
        role="status"
        className="flex items-center justify-center rounded-lg border border-red-800 bg-red-950/40 px-4 py-6 text-center"
      >
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-red-300">
            Pricing suspended
          </p>
          <p className="mt-1 text-xs text-red-400">
            No price is served while suspended — trading rules require a
            suspended state rather than a stale or guessed value.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-3">
      <PriceCell label={match.playerA} price={quote.pricePlayerA} />
      <PriceCell label={match.playerB} price={quote.pricePlayerB} />
    </div>
  );
}

function PriceCell({ label, price }: { label: string; price: number | null }) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900 px-4 py-3">
      <p className="truncate text-xs text-slate-400">{label}</p>
      <p className="mt-1 font-mono text-2xl text-slate-50">
        {price !== null ? price.toFixed(2) : "—"}
      </p>
    </div>
  );
}
