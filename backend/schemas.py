"""Pydantic request/response models — the API's response contract, matching
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
