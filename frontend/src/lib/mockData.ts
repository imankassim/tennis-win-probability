// Scripted scenario-library replay data (Journey 2 - first visible
// dashboard). The point sequences below are hand-scripted to walk through
// the target model scenarios from docs/architecture/charter.md: routine
// holds, break-point pressure against the favourite, a fight-back after
// dropping a set, a suspension (rain delay), and a stale quote after the
// resulting data gap - none of that needs a real archived match, since a
// completed archive can't produce a live suspension/data-gap event on
// demand (see docs/architecture/deployment.md).
//
// The probabilities themselves are real, though: buildMatchReplay (see
// scoring.ts) scores every scripted point through the actual backend
// pipeline (POST /probability/preview), the same Markov + ML + blend +
// calibration real matches use. Requires the backend to be running.

import { brk, buildMatchReplay, game, hold } from "./scoring";
import type { MatchScript } from "./scoring";
import type { MatchReplay, MatchSummary } from "./types";

const MATCH_SUMMARIES: MatchSummary[] = [
  {
    matchId: "demo_m001",
    tournament: "Riverside Open",
    round: "Quarterfinal",
    surface: "hard",
    bestOf: 3,
    date: "2026-08-14",
    playerA: "Player A",
    playerB: "Player B",
  },
  {
    matchId: "demo_m002",
    tournament: "Clairmont Clay Championships",
    round: "Semifinal",
    surface: "clay",
    bestOf: 3,
    date: "2026-05-22",
    playerA: "Player A",
    playerB: "Player B",
  },
];

// --- demo_m001: drop a set, save a break point under pressure, win the decider ---
const script001: MatchScript = {
  bestOf: 3,
  sets: [
    {
      // Set 1 - Player A (the favourite) trails early and drops the set:
      // "Favourite under early pressure" target scenario.
      games: [
        hold("player_a"),
        hold("player_b"),
        brk("player_a", 1, "Player B breaks early"),
        hold("player_b"),
        hold("player_a"),
        hold("player_b"),
        hold("player_a"),
        hold("player_b"),
        hold("player_a"),
        hold("player_b", 0, "Player B takes the first set 6-4"),
      ],
    },
    {
      // Set 2 - Player A saves a break point under pressure and closes it out:
      // "Break-point pressure" target scenario.
      games: [
        hold("player_a"),
        hold("player_b"),
        hold("player_a"),
        hold("player_b"),
        hold("player_a"),
        hold("player_b"),
        game(
          "player_a",
          ["player_b", "player_b", "player_b", "player_a", "player_a", "player_a", "player_a", "player_a"],
          "Player A saves three break points to hold",
        ),
        hold("player_b"),
        hold("player_a"),
        hold("player_b"),
        hold("player_a"),
        brk("player_b", 1, "Player A breaks to level the match at one set each"),
      ],
    },
    {
      // Set 3 - the decider: "Deciding-set recovery" target scenario.
      games: [
        hold("player_a"),
        hold("player_b"),
        hold("player_a"),
        brk("player_b", 1, "Player A breaks early in the decider"),
        hold("player_a"),
        hold("player_b"),
        hold("player_a"),
        hold("player_b"),
        hold("player_a", 0, "Player A wins the match 4-6, 7-5, 6-3"),
      ],
    },
  ],
};

// --- demo_m002: routine set, then a rain delay mid-second-set ---
const script002: MatchScript = {
  bestOf: 3,
  sets: [
    {
      games: [
        hold("player_a"),
        hold("player_b"),
        brk("player_a", 1, "Player B breaks"),
        hold("player_b"),
        hold("player_a"),
        hold("player_b"),
        hold("player_a"),
        hold("player_b"),
        hold("player_a"),
        hold("player_b", 0, "Player B takes the first set 6-4"),
      ],
    },
    {
      games: [
        hold("player_a"),
        hold("player_b"),
        hold("player_a"),
        hold("player_b"),
        hold("player_a", 0, "Rain delay called"),
        hold("player_b"),
        hold("player_a"),
        hold("player_b"),
        hold("player_a"),
        brk("player_b", 1, "Player A takes the second set 6-4"),
      ],
    },
    {
      games: [
        hold("player_a"),
        brk("player_b", 0, "Player A breaks"),
        hold("player_a"),
        hold("player_b"),
        hold("player_a"),
        brk("player_b", 1, "Player A breaks again"),
        hold("player_a", 0, "Player A wins the match 4-6, 6-4, 6-1"),
      ],
    },
  ],
};

async function buildDemoM001(): Promise<MatchReplay> {
  const { points, quotes } = await buildMatchReplay("demo_m001", script001);
  return { match: MATCH_SUMMARIES[0], points, quotes };
}

async function buildDemoM002(): Promise<MatchReplay> {
  const { points, quotes } = await buildMatchReplay("demo_m002", script002);

  // Splice in the rain delay: the point labelled "Rain delay called" is the
  // last point before suspension. Insert an extra, suspended quote right
  // after it (same point, a re-issued quote - no ball has been played, the
  // system is just reporting the suspended state), then mark the first
  // quote after resumption as stale (the data-gap target scenario: the
  // point event resumes before the pricing pipeline has caught up).
  const delayIndex = points.findIndex((p) => p.label === "Rain delay called");
  const delayPoint = points[delayIndex];
  const suspendedQuote = {
    ...quotes[delayIndex],
    probabilityRequestId: `req_demo_m002_${delayPoint.pointSequence}_suspended`,
    probabilityPlayerA: null,
    pricePlayerA: null,
    pricePlayerB: null,
    suspended: true,
  };
  quotes.splice(delayIndex + 1, 0, suspendedQuote);

  const resumedQuote = quotes[delayIndex + 2];
  if (resumedQuote) {
    resumedQuote.stale = true;
  }

  return { match: MATCH_SUMMARIES[1], points, quotes };
}

const REPLAYS: Record<string, () => Promise<MatchReplay>> = {
  demo_m001: buildDemoM001,
  demo_m002: buildDemoM002,
};

export function listMatches(): MatchSummary[] {
  return MATCH_SUMMARIES;
}

/** True for the scripted scenario-library matches (mock data); false for
 * anything that should be fetched from the real API instead. */
export function isScenarioLibraryMatch(matchId: string): boolean {
  return matchId in REPLAYS;
}

/** Returns null for an unknown match ID - the dashboard's error-state trigger. */
export function getMatchReplay(matchId: string): Promise<MatchReplay | null> {
  const build = REPLAYS[matchId];
  return build ? build() : Promise.resolve(null);
}
