"""Pydantic request/response models - the API's response contract, matching
docs/architecture/logical-architecture.md's example response."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class MatchSummarySchema(BaseModel):
    match_id: str
    tournament: str
    round: str
    surface: str
    best_of: int
    match_date: date
    player_a: str
    player_b: str


class PointSchema(BaseModel):
    point_no: int
    set_no: int
    game_no: int
    server: str
    point_winner: str
    sets_won_a: int
    sets_won_b: int
    games_won_a: int
    games_won_b: int


class OutcomeSchema(BaseModel):
    actual_winner: str
    final_score: str


class ReplayResponse(BaseModel):
    match: MatchSummarySchema
    points: list[PointSchema]
    outcome: OutcomeSchema | None


class MatchListResponse(BaseModel):
    matches: list[MatchSummarySchema]
    total: int


class ProbabilityRequest(BaseModel):
    match_id: str
    point_sequence: int


class MatchStateInterpretation(BaseModel):
    set: int
    games: str
    server: str
    break_point: bool


class ProbabilityResponse(BaseModel):
    probability_request_id: str
    match_id: str
    point_sequence: int
    interpretation: MatchStateInterpretation
    probability_player_a: float | None
    price_player_a: float | None
    price_player_b: float | None
    model_version: str
    fallback_used: bool
    suspended: bool
    # The Markov (analytic) and ML (learned) estimates computed
    # independently, before blend/calibration - so the dashboard can show
    # both alongside the final served probability, not just the combined
    # result (backend/probability.py's PricingResult). Unlike
    # probability_player_a, these stay populated even while suspended:
    # they're diagnostic/explanatory, not a served price, so showing them
    # doesn't imply a tradeable value the way a price would.
    markov_probability_a: float
    ml_probability_a: float | None


class ProbabilityPreviewRequest(BaseModel):
    """A hypothetical score state, not tied to any real match in the
    repository - see backend/main.py's /probability/preview for why this
    exists (the frontend's scripted scenario-library demo matches)."""

    best_of: int
    sets_a: int
    sets_b: int
    games_a: int
    games_b: int
    server: str
    points_a: int = 0
    points_b: int = 0
    # Matches pricing.markov.serve_rate.COLD_START_SERVE_RATE - the same
    # neutral default the real pipeline uses for a player with no serve
    # history, so a hypothetical demo player is treated exactly like a
    # real debut player would be, not given an arbitrary made-up rate.
    p_a_serve_rate: float = 0.6
    p_b_serve_rate: float = 0.6


class ProbabilityPreviewResponse(BaseModel):
    probability_player_a: float | None
    price_player_a: float | None
    price_player_b: float | None
    model_version: str
    fallback_used: bool
    suspended: bool
    markov_probability_a: float
    ml_probability_a: float | None


class OpsLatencySummary(BaseModel):
    n_quotes: int
    median_ms: float | None
    p95_ms: float | None


class OpsErrorSummary(BaseModel):
    fallback_count: int
    fallback_rate: float
    suspended_count: int
    suspended_rate: float
    model_version_counts: dict[str, int]


class OpsModelSummary(BaseModel):
    model_version: str
    trained_at: str
    n_training_matches: int
    n_calibration_matches: int
    calibration_brier: float
    calibration_log_loss: float
    calibration_ece: float


class OpsSummaryResponse(BaseModel):
    """Journey 19's dashboard, in API form: quality (the promoted model's
    own calibration-time evaluation - this system replays static
    historical data, so there's no live feed of outcomes to score served
    quotes against), latency and errors (both from the quote event log,
    Journey 7). `model` is null if no pipeline has been promoted yet
    (backend/probability.py's Markov-only fallback mode)."""

    latency: OpsLatencySummary
    errors: OpsErrorSummary
    model: OpsModelSummary | None
