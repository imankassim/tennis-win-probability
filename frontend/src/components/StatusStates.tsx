import Link from "next/link";

export function LoadingState() {
  return (
    <div role="status" aria-live="polite" className="space-y-3">
      <p className="text-sm text-slate-400">Loading match replay…</p>
      <div className="h-40 animate-pulse rounded-lg bg-slate-900" />
      <div className="h-56 animate-pulse rounded-lg bg-slate-900" />
    </div>
  );
}

export function ErrorState({ matchId }: { matchId: string }) {
  return (
    <div
      role="alert"
      className="rounded-lg border border-red-900 bg-red-950/30 p-6 text-center"
    >
      <p className="font-medium text-red-200">
        No match found for <span className="font-mono">{matchId}</span>.
      </p>
      <p className="mt-1 text-sm text-red-400">
        It may not be in the catalogue, or the ID was mistyped.
      </p>
      <Link
        href="/"
        className="mt-4 inline-block rounded-md border border-red-800 px-3 py-1.5 text-sm text-red-200 hover:bg-red-900/40"
      >
        Back to match selector
      </Link>
    </div>
  );
}
