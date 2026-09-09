// A minimal, honest tennis score-state machine used to build internally
// consistent mock replay data for the dashboard shell (Journey 2).
//
// This is deliberately simplified - no lets, no exact tiebreak serve
// rotation, tiebreaks collapsed to a single scripted point - because the
// goal here is a believable, self-consistent point sequence to wire the UI
// against, not a production match-state parser. The real match state
// parser (logical architecture component B1) is built in Journey 6 against
// real Sackmann point-by-point data.

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

/**
 * A deliberately crude score-differential heuristic - NOT the Markov or ML
 * engine built in Journeys 9 and 11. It exists only so the probability
 * chart and price ticker have something plausible to render against mock
 * data. Every quote it produces carries `modelVersion: "mock_placeholder_v0"`
 * so it can never be confused with a real estimate.
 */
function mockPlaceholderProbability(state: {
  setsA: number;
  setsB: number;
  gamesA: number;
  gamesB: number;
  server: Server;
  breakPoint: boolean;
}): number {
  let p = 0.5;
  p += 0.12 * (state.setsA - state.setsB);
  p += 0.02 * (state.gamesA - state.gamesB);
  p += state.server === "player_a" ? 0.04 : -0.04;
  if (state.breakPoint) {
    p += state.server === "player_a" ? -0.08 : 0.08;
  }
  return Math.min(0.97, Math.max(0.03, p));
}

const MOCK_MODEL_VERSION = "mock_placeholder_v0";

/** Expand a scripted match into a flat, sequenced list of point events and mock quotes. */
export function buildMatchReplay(
  matchId: string,
  script: MatchScript,
): { points: PointEvent[]; quotes: ProbabilityQuote[] } {
  const points: PointEvent[] = [];
  const quotes: ProbabilityQuote[] = [];
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

        const probabilityPlayerA = mockPlaceholderProbability({
          setsA,
          setsB,
          gamesA,
          gamesB,
          server: game.server,
          breakPoint,
        });
        const margin = 0.05;
        quotes.push({
          probabilityRequestId: `req_${matchId}_${pointSequence}`,
          matchId,
          pointSequence,
          interpretation,
          probabilityPlayerA,
          pricePlayerA: Number((1 / (probabilityPlayerA * (1 + margin))).toFixed(2)),
          pricePlayerB: Number((1 / ((1 - probabilityPlayerA) * (1 + margin))).toFixed(2)),
          modelVersion: MOCK_MODEL_VERSION,
          fallbackUsed: false,
          suspended: false,
        });
      });
    });

    if (gamesA > gamesB) setsA += 1;
    else setsB += 1;
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
