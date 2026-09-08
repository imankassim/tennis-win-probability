"use client";

import { useEffect, useRef } from "react";
import type { MatchSummary, PointEvent } from "@/lib/types";

function describePoint(point: PointEvent, match: MatchSummary): string {
  const winnerName = point.pointWinner === "player_a" ? match.playerA : match.playerB;
  if (point.label) return point.label;
  const bp = point.interpretation.breakPoint ? " (break point)" : "";
  return `Set ${point.setNo}, ${point.interpretation.games} — ${winnerName} wins the point${bp}`;
}

export function PointTicker({
  points,
  match,
}: {
  points: PointEvent[];
  match: MatchSummary;
}) {
  const endRef = useRef<HTMLLIElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }, [points.length]);

  return (
    <ol className="flex h-40 flex-col-reverse gap-1 overflow-y-auto rounded-lg border border-slate-800 bg-slate-900 p-2 text-xs">
      {[...points].reverse().map((point, i) => (
        <li
          key={point.pointSequence}
          ref={i === 0 ? endRef : undefined}
          className={
            point.interpretation.breakPoint
              ? "rounded px-2 py-1 text-amber-300"
              : "rounded px-2 py-1 text-slate-300"
          }
        >
          <span className="mr-2 font-mono text-slate-600">#{point.pointSequence}</span>
          {describePoint(point, match)}
        </li>
      ))}
    </ol>
  );
}
