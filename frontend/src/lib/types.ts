// Shared dashboard types.
//
// These mirror the API response contract in
// docs/architecture/logical-architecture.md so that swapping mock data for
// real FastAPI responses (Journey 5) does not require reshaping components.

export type Surface = "hard" | "clay" | "grass";

export interface MatchSummary {
  matchId: string;
  tournament: string;
  round: string;
  surface: Surface;
  bestOf: 3 | 5;
  date: string; // ISO date
  playerA: string;
  playerB: string;
}

export type Server = "player_a" | "player_b";

export interface MatchStateInterpretation {
  set: number;
  games: string; // e.g. "4-4"
  server: Server;
  breakPoint: boolean;
}

/** One point event in a match's point-by-point sequence. */
export interface PointEvent {
  pointSequence: number;
  setNo: number;
  gameNo: number;
  server: Server;
  pointWinner: Server;
  interpretation: MatchStateInterpretation;
  /** A short human-readable label for the point ticker, e.g. "Break point". */
  label?: string;
}

/**
 * One returned probability and price at one moment - the mock-data
 * equivalent of the /probability response contract.
 *
 * `probabilityPlayerA` and prices are null while `suspended` is true,
 * matching the data-quality rule that probabilities/prices are only ever
 * within-bounds values or null while suspended.
 */
export interface ProbabilityQuote {
  probabilityRequestId: string;
  matchId: string;
  pointSequence: number;
  interpretation: MatchStateInterpretation;
  probabilityPlayerA: number | null;
  pricePlayerA: number | null;
  pricePlayerB: number | null;
  modelVersion: string;
  fallbackUsed: boolean;
  suspended: boolean;
  /** True when this quote is older than the current point (data-gap scenario). */
  stale?: boolean;
  /**
   * The Markov (analytic formula) and ML (learned model) estimates
   * computed independently, before they're combined into
   * probabilityPlayerA - so the chart can show each one as its own
   * line, not just the final blended/calibrated result. Undefined for
   * the scenario library's scripted mock data, which has no real
   * blend behind it; markovProbabilityA is always present for real
   * matches, mlProbabilityA only once a pipeline has been promoted.
   */
  markovProbabilityA?: number;
  mlProbabilityA?: number | null;
}

export interface MatchReplay {
  match: MatchSummary;
  points: PointEvent[];
  quotes: ProbabilityQuote[];
}

export type PageState = "loading" | "success" | "error";

/** Journey 19's monitoring dashboard, as data - see GET /ops/summary. */
export interface OpsSummary {
  latency: {
    nQuotes: number;
    medianMs: number | null;
    p95Ms: number | null;
  };
  errors: {
    fallbackCount: number;
    fallbackRate: number;
    suspendedCount: number;
    suspendedRate: number;
    modelVersionCounts: Record<string, number>;
  };
  model: {
    modelVersion: string;
    trainedAt: string;
    nTrainingMatches: number;
    nCalibrationMatches: number;
    calibrationBrier: number;
    calibrationLogLoss: number;
    calibrationEce: number;
  } | null;
}
