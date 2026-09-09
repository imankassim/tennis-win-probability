import type { ProbabilityQuote } from "@/lib/types";

const WIDTH = 600;
const HEIGHT = 220;
const PAD = 28;

/**
 * A small inline SVG line chart of player A's win probability over the
 * match so far. Suspended points (probability null) break the line rather
 * than interpolating across them - the chart must never imply a value
 * that was never served.
 */
export function ProbabilityChart({
  quotes,
  playerAName,
  playerBName,
}: {
  quotes: ProbabilityQuote[];
  playerAName: string;
  playerBName: string;
}) {
  const n = quotes.length;
  const x = (i: number) => PAD + (i / Math.max(1, n - 1)) * (WIDTH - PAD * 2);
  const y = (p: number) => PAD + (1 - p) * (HEIGHT - PAD * 2);

  const segments: { x: number; y: number }[][] = [];
  let current: { x: number; y: number }[] = [];
  quotes.forEach((q, i) => {
    if (q.probabilityPlayerA === null) {
      if (current.length) segments.push(current);
      current = [];
      return;
    }
    current.push({ x: x(i), y: y(q.probabilityPlayerA) });
  });
  if (current.length) segments.push(current);

  const last = quotes[quotes.length - 1];
  const lastP = last?.probabilityPlayerA;

  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-xs text-slate-400">
        <span>{playerAName} win probability</span>
        <span className="font-mono text-slate-200">
          {lastP !== null && lastP !== undefined ? `${Math.round(lastP * 100)}%` : "—"}
        </span>
      </div>
      <svg
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        className="w-full overflow-visible rounded-lg border border-slate-800 bg-slate-900"
        role="img"
        aria-label={`Win probability for ${playerAName} over the course of the match`}
      >
        {/* 50% reference line */}
        <line
          x1={PAD}
          x2={WIDTH - PAD}
          y1={y(0.5)}
          y2={y(0.5)}
          stroke="currentColor"
          className="text-slate-700"
          strokeDasharray="4 4"
        />
        <text x={WIDTH - PAD} y={y(0.5) - 4} textAnchor="end" className="fill-slate-600 text-[10px]">
          50%
        </text>

        {segments.map((seg, si) => (
          <polyline
            key={si}
            points={seg.map((pt) => `${pt.x},${pt.y}`).join(" ")}
            fill="none"
            stroke="#38bdf8"
            strokeWidth={2}
          />
        ))}

        {lastP !== null && lastP !== undefined && (
          <circle cx={x(n - 1)} cy={y(lastP)} r={4} fill="#38bdf8" />
        )}
      </svg>
      <div className="mt-1 flex justify-between text-[11px] text-slate-500">
        <span>{playerAName}</span>
        <span>{playerBName}</span>
      </div>
    </div>
  );
}
