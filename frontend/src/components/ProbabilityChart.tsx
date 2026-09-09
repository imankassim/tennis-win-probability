import type { ProbabilityQuote } from "@/lib/types";

const WIDTH = 600;
const HEIGHT = 220;
const PAD = 28;

interface Series {
  key: string;
  label: string;
  color: string;
  dashed?: boolean;
  strokeWidth: number;
  getValue: (q: ProbabilityQuote) => number | null | undefined;
}

const FINAL_SERIES: Series = {
  key: "final",
  label: "Served (blend + calibration)",
  color: "#38bdf8",
  strokeWidth: 2.5,
  getValue: (q) => q.probabilityPlayerA,
};

const MARKOV_SERIES: Series = {
  key: "markov",
  label: "Markov (math formula)",
  color: "#f59e0b",
  dashed: true,
  strokeWidth: 1.5,
  getValue: (q) => q.markovProbabilityA,
};

const ML_SERIES: Series = {
  key: "ml",
  label: "ML (learned model)",
  color: "#a78bfa",
  dashed: true,
  strokeWidth: 1.5,
  getValue: (q) => q.mlProbabilityA,
};

function buildSegments(quotes: ProbabilityQuote[], series: Series, x: (i: number) => number, y: (p: number) => number) {
  const segments: { x: number; y: number }[][] = [];
  let current: { x: number; y: number }[] = [];
  quotes.forEach((q, i) => {
    const value = series.getValue(q);
    if (value === null || value === undefined) {
      if (current.length) segments.push(current);
      current = [];
      return;
    }
    current.push({ x: x(i), y: y(value) });
  });
  if (current.length) segments.push(current);
  return segments;
}

/**
 * A small inline SVG line chart of player A's win probability over the
 * match so far. Plots up to three lines when the data has them (real
 * matches; the scenario library's scripted mock data only ever has the
 * "served" line): the Markov analytic formula and the ML model's own
 * estimate, computed independently, alongside the final value actually
 * served after blending the two and calibrating the result - so it's
 * possible to see not just what price was quoted, but *why* (e.g. the
 * two estimates disagreeing, or one pulling the served line toward it).
 *
 * Suspended points (the served line's value is null) break that line
 * rather than interpolating across them - the chart must never imply a
 * served value that was never actually served. The Markov/ML lines stay
 * connected through a suspended point when they have real values there
 * (trading_rules can suspend the final price while the underlying
 * estimates remain genuinely computed) - unbroken, real numbers on
 * those two lines are useful context for *why* it got suspended.
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

  const hasMarkov = quotes.some((q) => q.markovProbabilityA !== undefined);
  const hasMl = quotes.some((q) => q.mlProbabilityA !== null && q.mlProbabilityA !== undefined);
  const series = [
    ...(hasMarkov ? [MARKOV_SERIES] : []),
    ...(hasMl ? [ML_SERIES] : []),
    FINAL_SERIES,
  ];

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

        {series.map((s) =>
          buildSegments(quotes, s, x, y).map((seg, si) => (
            <polyline
              key={`${s.key}-${si}`}
              points={seg.map((pt) => `${pt.x},${pt.y}`).join(" ")}
              fill="none"
              stroke={s.color}
              strokeWidth={s.strokeWidth}
              strokeDasharray={s.dashed ? "5 4" : undefined}
            />
          )),
        )}

        {lastP !== null && lastP !== undefined && (
          <circle cx={x(n - 1)} cy={y(lastP)} r={4} fill={FINAL_SERIES.color} />
        )}
      </svg>

      {(hasMarkov || hasMl) && (
        <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-slate-400">
          {series.map((s) => (
            <span key={s.key} className="flex items-center gap-1.5">
              <span
                className="inline-block h-0.5 w-4"
                style={{
                  backgroundColor: s.dashed ? "transparent" : s.color,
                  borderTop: s.dashed ? `2px dashed ${s.color}` : undefined,
                }}
              />
              {s.label}
            </span>
          ))}
        </div>
      )}

      <div className="mt-1 flex justify-between text-[11px] text-slate-500">
        <span>{playerAName}</span>
        <span>{playerBName}</span>
      </div>
    </div>
  );
}
