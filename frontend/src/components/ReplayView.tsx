"use client";

import { useEffect, useRef, useState } from "react";
import { getRealMatchReplay } from "@/lib/api";
import { getMatchReplay, isScenarioLibraryMatch } from "@/lib/mockData";
import type { MatchReplay, PageState } from "@/lib/types";
import { ErrorState, LoadingState } from "./StatusStates";
import { ModelVersionBadge } from "./ModelVersionBadge";
import { PriceTicker } from "./PriceTicker";
import { ProbabilityChart } from "./ProbabilityChart";
import { PointTicker } from "./PointTicker";
import { PlaybackControls } from "./PlaybackControls";

const PLAY_INTERVAL_MS = 700;

/**
 * Renders one match's replay. The parent mounts this with `key={matchId}`
 * (see the replay route) so that switching matches always starts from a
 * fresh "loading" state instead of needing an effect to reset it.
 */
export function ReplayView({ matchId }: { matchId: string }) {
  const [pageState, setPageState] = useState<PageState>("loading");
  const [replay, setReplay] = useState<MatchReplay | null>(null);
  const [quoteIndex, setQuoteIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    let cancelled = false;

    const onLoaded = (data: MatchReplay | null) => {
      if (cancelled) return;
      if (!data) {
        setReplay(null);
        setPageState("error");
        return;
      }
      setReplay(data);
      setQuoteIndex(0);
      setPageState("success");
    };

    const fetchReplay = isScenarioLibraryMatch(matchId)
      ? getMatchReplay(matchId)
      : getRealMatchReplay(matchId);

    fetchReplay.then((data) => onLoaded(data)).catch(() => onLoaded(null));
    return () => {
      cancelled = true;
    };
  }, [matchId]);

  const maxIndex = replay ? replay.quotes.length - 1 : 0;

  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  useEffect(() => {
    if (!isPlaying || !replay) return;
    intervalRef.current = setInterval(() => {
      setQuoteIndex((i) => {
        if (i >= replay.quotes.length - 1) {
          setIsPlaying(false);
          return i;
        }
        return i + 1;
      });
    }, PLAY_INTERVAL_MS);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [isPlaying, replay]);

  if (pageState === "loading") return <LoadingState />;
  if (pageState === "error" || !replay) return <ErrorState matchId={matchId} />;

  const currentQuote = replay.quotes[quoteIndex];
  const visibleQuotes = replay.quotes.slice(0, quoteIndex + 1);
  const visiblePoints = replay.points.filter(
    (p) => p.pointSequence <= currentQuote.pointSequence,
  );

  return (
    <div className="space-y-4">
      <header>
        <p className="text-xs uppercase tracking-wide text-slate-500">
          {replay.match.tournament} - {replay.match.round}
        </p>
        <h1 className="text-xl font-semibold text-slate-100">
          {replay.match.playerA} <span className="text-slate-500">vs</span>{" "}
          {replay.match.playerB}
        </h1>
        <p className="text-xs text-slate-500">
          {replay.match.surface} · best of {replay.match.bestOf} · {replay.match.date}
        </p>
      </header>

      <ModelVersionBadge quote={currentQuote} />

      <ProbabilityChart
        quotes={visibleQuotes}
        playerAName={replay.match.playerA}
        playerBName={replay.match.playerB}
      />

      <PriceTicker quote={currentQuote} match={replay.match} />

      <PlaybackControls
        index={quoteIndex}
        max={maxIndex}
        isPlaying={isPlaying}
        onChange={(i) => {
          setIsPlaying(false);
          setQuoteIndex(i);
        }}
        onTogglePlay={() => setIsPlaying((p) => !p)}
      />

      <PointTicker points={visiblePoints} match={replay.match} />
    </div>
  );
}
