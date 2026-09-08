"""FastAPI application (Journey 5): /health, /replay/{match_id}, /probability.

Reads real ingested data if COURTEDGE_DATA_DIR is set to a directory
containing charting-*-matches.csv and charting-*-points-*.csv (see
database/README.md); otherwise serves the synthetic demo fixture
(backend/fixtures.py) so the app runs out of the box.

break_point in the probability response is always False for now — flagging
it correctly requires the within-game point tally, which is the match-state
parser's job (Journey 6), not this API's.
"""

from __future__ import annotations

import itertools
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException

from backend.fixtures import demo_repository_data
from backend.probability import MODEL_VERSION, compute_quote
from backend.repository import InMemoryMatchRepository, MatchRepository, load_from_csv
from backend.schemas import (
    MatchStateInterpretation,
    MatchSummarySchema,
    OutcomeSchema,
    PointSchema,
    ProbabilityRequest,
    ProbabilityResponse,
    ReplayResponse,
)

app = FastAPI(title="CourtEdge API")

_request_ids = itertools.count(1)


def _build_repository() -> MatchRepository:
    data_dir = os.environ.get("COURTEDGE_DATA_DIR")
    if data_dir:
        directory = Path(data_dir)
        matches_csv = next(directory.glob("charting-*-matches.csv"))
        points_csv = next(directory.glob("charting-*-points-*.csv"))
        return load_from_csv(matches_csv, points_csv)
    matches, players, points_by_match = demo_repository_data()
    return InMemoryMatchRepository(matches, players, points_by_match)


repository: MatchRepository = _build_repository()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/replay/{match_id}", response_model=ReplayResponse)
def get_replay(match_id: str) -> ReplayResponse:
    match = repository.get_match(match_id)
    if match is None:
        raise HTTPException(status_code=404, detail=f"No match found for {match_id!r}")

    player_a = repository.get_player(match.player_a_id)
    player_b = repository.get_player(match.player_b_id)
    points = repository.get_points(match_id)
    outcome = repository.get_outcome(match_id)

    return ReplayResponse(
        match=MatchSummarySchema(
            match_id=match.match_id,
            tournament=match.tournament,
            round=match.round,
            surface=match.surface,
            best_of=match.best_of,
            match_date=match.match_date,
            player_a=player_a.name if player_a else match.player_a_id,
            player_b=player_b.name if player_b else match.player_b_id,
        ),
        points=[
            PointSchema(
                point_no=p.point_no,
                set_no=p.set_no,
                game_no=p.game_no,
                server=p.server,
                point_winner=p.point_winner,
                sets_won_a=p.sets_won_a,
                sets_won_b=p.sets_won_b,
                games_won_a=p.games_won_a,
                games_won_b=p.games_won_b,
            )
            for p in points
        ],
        outcome=OutcomeSchema(actual_winner=outcome.actual_winner, final_score=outcome.final_score)
        if outcome
        else None,
    )


@app.post("/probability", response_model=ProbabilityResponse)
def post_probability(request: ProbabilityRequest) -> ProbabilityResponse:
    match = repository.get_match(request.match_id)
    if match is None:
        raise HTTPException(status_code=404, detail=f"No match found for {request.match_id!r}")

    points = repository.get_points(request.match_id)
    matching = [p for p in points if p.point_no == request.point_sequence]
    if not matching:
        raise HTTPException(
            status_code=404,
            detail=f"No point {request.point_sequence} recorded for match {request.match_id!r}",
        )
    point = matching[0]

    probability_a, price_a, price_b = compute_quote(
        sets_won_a=point.sets_won_a,
        sets_won_b=point.sets_won_b,
        games_won_a=point.games_won_a,
        games_won_b=point.games_won_b,
    )

    return ProbabilityResponse(
        probability_request_id=f"req_{next(_request_ids):x}",
        match_id=request.match_id,
        point_sequence=request.point_sequence,
        interpretation=MatchStateInterpretation(
            set=point.set_no,
            games=f"{point.games_won_a}-{point.games_won_b}",
            server=point.server,
            break_point=False,
        ),
        probability_player_a=probability_a,
        price_player_a=price_a,
        price_player_b=price_b,
        model_version=MODEL_VERSION,
        fallback_used=False,
        suspended=False,
    )
