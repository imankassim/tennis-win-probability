"use client";

export function PlaybackControls({
  index,
  max,
  isPlaying,
  onChange,
  onTogglePlay,
}: {
  index: number;
  max: number;
  isPlaying: boolean;
  onChange: (index: number) => void;
  onTogglePlay: () => void;
}) {
  return (
    <div className="flex items-center gap-3">
      <button
        type="button"
        onClick={() => onChange(Math.max(0, index - 1))}
        disabled={index === 0}
        aria-label="Previous point"
        className="rounded-md border border-slate-700 px-2.5 py-1.5 text-sm text-slate-200 hover:bg-slate-800 disabled:opacity-40"
      >
        ◂
      </button>
      <button
        type="button"
        onClick={onTogglePlay}
        aria-label={isPlaying ? "Pause replay" : "Play replay"}
        className="rounded-md border border-slate-700 px-3 py-1.5 text-sm text-slate-200 hover:bg-slate-800"
      >
        {isPlaying ? "Pause" : "Play"}
      </button>
      <button
        type="button"
        onClick={() => onChange(Math.min(max, index + 1))}
        disabled={index === max}
        aria-label="Next point"
        className="rounded-md border border-slate-700 px-2.5 py-1.5 text-sm text-slate-200 hover:bg-slate-800 disabled:opacity-40"
      >
        ▸
      </button>
      <input
        type="range"
        min={0}
        max={max}
        value={index}
        onChange={(e) => onChange(Number(e.target.value))}
        aria-label="Scrub through the match replay"
        className="flex-1 accent-lime-400"
      />
      <span className="w-16 shrink-0 text-right font-mono text-xs text-slate-400">
        {index + 1} / {max + 1}
      </span>
    </div>
  );
}
