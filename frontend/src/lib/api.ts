// Client for the real backend (backend/main.py), added in Journey 6.
//
// The scripted demo matches (mockData.ts) still exist as a separate
// "scenario library" — they demonstrate page states (suspended, stale)
// that real historical data can't produce, since suspension is a live-feed
// concept with no equivalent in a completed match archive. This module is
// for browsing and replaying *real* matches through the actual API.

import type { MatchReplay, MatchSummary, PointEvent, ProbabilityQuote, Surface } from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

interface ApiMatchSummary {
  match_id: string;
  tournament: string;
  round: string;
  surface: string;
  best_of: number;
  match_date: string;
  player_a: string;
  player_b: string;
}

interface ApiPoint {
  point_no: number;
  set_no: number;
  game_no: number;
  server: "player_a" | "player_b";
  point_winner: "player_a" | "player_b";
  sets_won_a: number;
  sets_won_b: number;
  games_won_a: number;
  games_won_b: number;
}

interface ApiOutcome {
  actual_winner: "player_a" | "player_b";
  final_score: string;
}

interface ApiReplayResponse {
  match: ApiMatchSummary;
  points: ApiPoint[];
  outcome: ApiOutcome | null;
}

interface ApiMatchListResponse {
  matches: ApiMatchSummary[];
  total: number;
}

interface ApiProbabilityResponse {
  probability_request_id: string;
  match_id: string;
  point_sequence: number;
  interpretation: {
    set: number;
    games: string;
    server: "player_a" | "player_b";
    break_point: boolean;
  };
  probability_player_a: number | null;
  price_player_a: number | null;
  price_player_b: number | null;
  model_version: string;
  fallback_used: boolean;
  suspended: boolean;
}

function adaptMatchSummary(m: ApiMatchSummary): MatchSummary {
  return {
    matchId: m.match_id,
    tournament: m.tournament,
    round: m.round,
    surface: m.surface.toLowerCase() as Surface,
    bestOf: m.best_of as 3 | 5,
    date: m.match_date,
    playerA: m.player_a,
    playerB: m.player_b,
  };
}

export async function listRealMatches(filters?: {
  tournament?: string;
  surface?: string;
}): Promise<MatchSummary[]> {
  const params = new URLSearchParams();
  if (filters?.tournament) params.set("tournament", filters.tournament);
  if (filters?.surface) params.set("surface", filters.surface);
  const query = params.toString();
  const res = await fetch(`${API_BASE_URL}/matches${query ? `?${query}` : ""}`);
  if (!res.ok) throw new Error(`Failed to list matches: ${res.status}`);
  const body: ApiMatchListResponse = await res.json();
  return body.matches.map(adaptMatchSummary);
}

async function fetchProbability(
  matchId: string,
  pointSequence: number,
): Promise<ProbabilityQuote> {
  const res = await fetch(`${API_BASE_URL}/probability`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ match_id: matchId, point_sequence: pointSequence }),
  });
  if (!res.ok) throw new Error(`Failed to fetch probability for point ${pointSequence}`);
  const q: ApiProbabilityResponse = await res.json();
  return {
    probabilityRequestId: q.probability_request_id,
    matchId: q.match_id,
    pointSequence: q.point_sequence,
    interpretation: {
      set: q.interpretation.set,
      games: q.interpretation.games,
      server: q.interpretation.server,
      breakPoint: q.interpretation.break_point,
    },
    probabilityPlayerA: q.probability_player_a,
    pricePlayerA: q.price_player_a,
    pricePlayerB: q.price_player_b,
    modelVersion: q.model_version,
    fallbackUsed: q.fallback_used,
    suspended: q.suspended,
  };
}

/**
 * Fetches a real match's full replay: the point list plus a probability
 * quote for every point. The backend has no bulk-quote endpoint yet, so
 * this issues one request per point in parallel — fine for a match-sized
 * point count on localhost, but a real optimisation candidate later.
 */
export async function getRealMatchReplay(matchId: string): Promise<MatchReplay> {
  const res = await fetch(`${API_BASE_URL}/replay/${encodeURIComponent(matchId)}`);
  if (!res.ok) throw new Error(`No match found for ${matchId}`);
  const body: ApiReplayResponse = await res.json();

  const quotes = await Promise.all(
    body.points.map((p) => fetchProbability(matchId, p.point_no)),
  );
  const quoteBySequence = new Map(quotes.map((q) => [q.pointSequence, q]));

  const points: PointEvent[] = body.points.map((p) => {
    const quote = quoteBySequence.get(p.point_no);
    return {
      pointSequence: p.point_no,
      setNo: p.set_no,
      gameNo: p.game_no,
      server: p.server,
      pointWinner: p.point_winner,
      interpretation: quote
        ? quote.interpretation
        : {
            set: p.set_no,
            games: `${p.games_won_a}-${p.games_won_b}`,
            server: p.server,
            breakPoint: false,
          },
    };
  });

  return {
    match: adaptMatchSummary(body.match),
    points,
    quotes,
  };
}
