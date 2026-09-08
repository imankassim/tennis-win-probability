import Link from "next/link";
import { ReplayView } from "@/components/ReplayView";

export default async function ReplayPage({
  params,
}: {
  params: Promise<{ matchId: string }>;
}) {
  const { matchId } = await params;

  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-10">
      <Link href="/" className="text-xs text-slate-500 hover:text-slate-300">
        ← All matches
      </Link>
      <div className="mt-4">
        <ReplayView key={matchId} matchId={matchId} />
      </div>
    </div>
  );
}
