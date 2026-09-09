// A minimal, honest tennis score-state machine used to build the
// scenario library's scripted replay data (Journey 2).
//
// This is deliberately simplified - no lets, no exact tiebreak serve
// rotation, tiebreaks collapsed to a single scripted point - because the
// goal here is a believable, self-consistent point sequence to demonstrate
// specific target scenarios (docs/architecture/charter.md), not a
// production match-state parser. The real match state parser (logical
// architecture component B1) is match_state.py, built against real
// archive data.
//
// Every point's probability is real model output, not a fabricated
// heuristic: buildMatchReplay calls the backend's POST /probability/preview
// (see lib/api.ts) for each point, running the same Markov + ML + blend +
// calibration pipeline real matches use, just against a hypothetical state
// instead of a real match_id. The two demo players have no real serve or
// context history, so they're scored exactly like any real debut player
// would be (cold-start serve rate, neutral context features) - not given
// arbitrary made-up numbers. Requires the backend to be running; unlike
// before this change, the scenario library is no longer fully standalone.

import { previewProbability } from "./api";
import type { PointEvent, ProbabilityQuote, Server } from "./types";

const other = (p: Server): Server => (p === "player_a" ? "player_b" : "player_a");

interface GameScriptStep {
  /** Who serves this game. */
  server: Server;
  /** Ordered list of who wins each point within the game (or the single tiebreak-deciding point). */
  points: Server[];
  /** True if 6-6 in games - this "game" represents a whole tiebreak, decided by its single point. */
  isTiebreak?: boolean;
  label?: string;
}

export interface SetScript {
  games: GameScriptStep[];
}

export interface MatchScript {
  bestOf: 3 | 5;
  sets: SetScript[];
}

interface PreviewState {
  setsA: number;
  setsB: number;
  gamesA: number;
  gamesB: number;
  server: Server;
  pointsA: number;
  pointsB: number;
}

/** Expand a scripted match into a flat, sequenced list of point events,
 * then score every point through the real backend pipeline in parallel
 * (POST /probability/preview) - the same pattern lib/api.ts's
 * getRealMatchReplay already uses for real matches. */
export async function buildMatchReplay(
  matchId: string,
  script: MatchScript,
): Promise<{ points: PointEvent[]; quotes: ProbabilityQuote[] }> {
  const points: PointEvent[] = [];
  const previewStates: PreviewState[] = [];
  let pointSequence = 0;
  let setsA = 0;
  let setsB = 0;

  script.sets.forEach((set, setIdx) => {
    const setNo = setIdx + 1;
    let gamesA = 0;
    let gamesB = 0;

    set.games.forEach((game, gameIdx) => {
      const gameNo = gameIdx + 1;
      let pointsA = 0;
      let pointsB = 0;

      game.points.forEach((winner, i) => {
        pointSequence += 1;

        if (game.isTiebreak) {
          // Collapse the whole tiebreak into its single scripted outcome.
          if (winner === "player_a") gamesA += 1;
          else gamesB += 1;
        } else if (winner === "player_a") {
          pointsA += 1;
        } else {
          pointsB += 1;
        }

        const receiver = other(game.server);
        const receiverPoints = receiver === "player_a" ? pointsA : pointsB;
        const serverPoints = receiver === "player_a" ? pointsB : pointsA;
        // Receiver is one point from winning the game: the next point would
        // put them at >=4 with a lead of >=2 over the server.
        const breakPoint =
          !game.isTiebreak && receiverPoints >= 3 && receiverPoints - serverPoints >= 1;

        const isLastPointOfGame = i === game.points.length - 1;
        if (isLastPointOfGame && !game.isTiebreak) {
          if (pointsA > pointsB) gamesA += 1;
          else gamesB += 1;
        }

        const interpretation = {
          set: setNo,
          games: `${gamesA}-${gamesB}`,
          server: game.server,
          breakPoint,
        };

        points.push({
          pointSequence,
          setNo,
          gameNo,
          server: game.server,
          pointWinner: winner,
          interpretation,
          label: isLastPointOfGame ? game.label : undefined,
        });

        previewStates.push({
          setsA,
          setsB,
          gamesA,
          gamesB,
          server: game.server,
          // Tiebreaks are collapsed to one scripted point with no
          // meaningful in-game point score to report.
          pointsA: game.isTiebreak ? 0 : pointsA,
          pointsB: game.isTiebreak ? 0 : pointsB,
        });
      });
    });

    if (gamesA > gamesB) setsA += 1;
    else setsB += 1;
  });

  const previews = await Promise.all(
    previewStates.map((s) =>
      previewProbability({
        bestOf: script.bestOf,
        setsA: s.setsA,
        setsB: s.setsB,
        gamesA: s.gamesA,
        gamesB: s.gamesB,
        server: s.server,
        pointsA: s.pointsA,
        pointsB: s.pointsB,
      }),
    ),
  );

  const quotes: ProbabilityQuote[] = points.map((point, i) => {
    const preview = previews[i];
    return {
      probabilityRequestId: `req_${matchId}_${point.pointSequence}`,
      matchId,
      pointSequence: point.pointSequence,
      interpretation: point.interpretation,
      probabilityPlayerA: preview.probabilityPlayerA,
      pricePlayerA: preview.pricePlayerA,
      pricePlayerB: preview.pricePlayerB,
      modelVersion: preview.modelVersion,
      fallbackUsed: preview.fallbackUsed,
      suspended: preview.suspended,
      markovProbabilityA: preview.markovProbabilityA,
      mlProbabilityA: preview.mlProbabilityA,
    };
  });

  return { points, quotes };
}

/** A routine hold: the receiver wins `oppPoints` points (0, 1 or 2 - i.e. love/15/30) before the server closes it out. */
export function hold(server: Server, oppPoints: 0 | 1 | 2 = 0, label?: string): GameScriptStep {
  const receiver = other(server);
  const points: Server[] = [
    ...Array(oppPoints).fill(receiver),
    ...Array(4).fill(server),
  ];
  return { server, points, label };
}

/** A routine break: the server wins `serverPoints` points (0, 1 or 2) before the receiver closes it out. */
export function brk(server: Server, serverPoints: 0 | 1 | 2 = 0, label?: string): GameScriptStep {
  const receiver = other(server);
  const points: Server[] = [
    ...Array(serverPoints).fill(server),
    ...Array(4).fill(receiver),
  ];
  return { server, points, label };
}

/** A tiebreak, collapsed to its single deciding point. */
export function tiebreak(server: Server, winner: Server, label?: string): GameScriptStep {
  return { server, points: [winner], isTiebreak: true, label };
}

/** A game scripted point-by-point, for marquee moments (e.g. a saved break point). */
export function game(server: Server, points: Server[], label?: string): GameScriptStep {
  return { server, points, label };
}
