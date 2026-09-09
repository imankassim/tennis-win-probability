"""FastAPI application: /health, /matches, /replay/{match_id}, /probability.

Reads real ingested data if COURTEDGE_DATA_DIR is set to a directory
containing charting-*-matches.csv and charting-*-points-*.csv (see
database/README.md); otherwise serves the synthetic demo fixture
(backend/fixtures.py) so the app runs out of the box.
"""

from __future__ import annotations

import itertools
import os
import time
from datetime import date
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.event_log import log_quote, read_quote_log
from backend.fixtures import demo_repository_data
from backend.match_state import compute_break_point, game_score_before
from backend.probability import compute_probability, load_artefacts
from backend.repository import InMemoryMatchRepository, MatchRepository, load_from_csv
from database.models import Match
from evaluation.metrics import percentile
from pricing.markov.serve_rate import COLD_START_SERVE_RATE, bulk_shrunk_serve_rates
from pricing.ml.features import compute_match_context_features
from trading_rules.rules import DEFAULT_MARGIN, WIDENED_MARGIN, apply_trading_rules
from backend.schemas import (
    MatchListResponse,
    MatchStateInterpretation,
    MatchSummarySchema,
    OpsErrorSummary,
    OpsLatencySummary,
    OpsModelSummary,
    OpsSummaryResponse,
    OutcomeSchema,
    PointSchema,
    ProbabilityPreviewRequest,
    ProbabilityPreviewResponse,
    ProbabilityRequest,
    ProbabilityResponse,
    ReplayResponse,
)

app = FastAPI(title="CourtEdge API")

# The dashboard (frontend/) runs on a different origin in development
# (Next.js dev server vs uvicorn). Wide open for now since this is a
# research prototype with no auth/session state; tighten before any real
# deployment (Journey 20).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_request_ids = itertools.count(1)


def _match_summary(match, repo: MatchRepository) -> MatchSummarySchema:
    player_a = repo.get_player(match.player_a_id)
    player_b = repo.get_player(match.player_b_id)
    return MatchSummarySchema(
        match_id=match.match_id,
        tournament=match.tournament,
        round=match.round,
        surface=match.surface,
        best_of=match.best_of,
        match_date=match.match_date,
        player_a=player_a.name if player_a else match.player_a_id,
        player_b=player_b.name if player_b else match.player_b_id,
    )


def _build_repository() -> MatchRepository:
    data_dir = os.environ.get("COURTEDGE_DATA_DIR")
    if data_dir:
        directory = Path(data_dir)
        matches_csv = next(directory.glob("charting-*-matches.csv"))
        # All matching points files, not just the first - the data
        # directory may hold one per decade (or a smaller sample
        # alongside the full files); real match_ids never repeat across
        # them, same as database/ingestion/run.py.
        points_csvs = sorted(directory.glob("charting-*-points-*.csv"))
        return load_from_csv(matches_csv, *points_csvs)
    matches, players, points_by_match = demo_repository_data()
    return InMemoryMatchRepository(matches, players, points_by_match)


repository: MatchRepository = _build_repository()

# Serve rates only depend on a match's own date and the archive up to it,
# not on which point is being priced - computed once per match, at
# startup, rather than lazily per request. Lazily calling
# estimate_match_serve_rates on first use (this module's original
# approach) re-scans the whole prior archive for whichever match happens
# to be requested first - measured directly at this data's scale: ~750ms
# for a single match's first request against the full ~900K-point
# archive, vs ~0.2ms once cached. bulk_shrunk_serve_rates computes every
# match's rate in one archive pass up front instead (a few seconds at
# startup, comparable to the time already spent building the repository),
# so no single request ever pays that cost.
_serve_rate_cache: dict[str, tuple[float, float]] = bulk_shrunk_serve_rates(
    repository.list_matches(), repository.all_points_by_match()
)

# Same reasoning as the serve-rate cache above, for the ML model's context
# features (form/surface/h2h/Elo): computed once per match in one archive
# pass at startup, not per request. Uses the exact same bulk function the
# promotion script (pricing/promote_model.py) trained against, so a live
# request scores the identical feature the model learned from - no
# separate "live" reimplementation to drift out of sync.
_context_cache: dict[str, dict[str, float]] = compute_match_context_features(
    repository.list_matches(), repository.all_outcomes()
)

# The promoted pipeline (Journey 17), if pricing/promote_model.py has been
# run against this data. None on a fresh clone - compute_probability
# degrades to Markov-only in that case (see backend/probability.py).
_artefacts = load_artefacts()


def _serve_rates_for(match) -> tuple[float, float]:
    return _serve_rate_cache.get(match.match_id, (COLD_START_SERVE_RATE, COLD_START_SERVE_RATE))


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ops/summary", response_model=OpsSummaryResponse)
def ops_summary() -> OpsSummaryResponse:
    """Journey 19's monitoring dashboard, as data: latency and error
    rates from every quote served since the log file was last cleared
    (Journey 7's event log), plus the promoted pipeline's own
    calibration-time quality snapshot (None if nothing has been
    promoted - see backend/probability.py)."""
    records = read_quote_log()
    latencies = [r["latency_ms"] for r in records]
    n = len(records)

    fallback_count = sum(1 for r in records if r["fallback_used"])
    suspended_count = sum(1 for r in records if r["suspended"])
    model_version_counts: dict[str, int] = {}
    for r in records:
        model_version_counts[r["model_version"]] = model_version_counts.get(r["model_version"], 0) + 1

    model_summary = (
        OpsModelSummary(
            model_version=_artefacts.model_version,
            trained_at=_artefacts.trained_at,
            n_training_matches=_artefacts.n_training_matches,
            n_calibration_matches=_artefacts.n_calibration_matches,
            calibration_brier=_artefacts.calibration_brier,
            calibration_log_loss=_artefacts.calibration_log_loss,
            calibration_ece=_artefacts.calibration_ece,
        )
        if _artefacts is not None
        else None
    )

    return OpsSummaryResponse(
        latency=OpsLatencySummary(
            n_quotes=n,
            median_ms=percentile(latencies, 50) if n else None,
            p95_ms=percentile(latencies, 95) if n else None,
        ),
        errors=OpsErrorSummary(
            fallback_count=fallback_count,
            fallback_rate=fallback_count / n if n else 0.0,
            suspended_count=suspended_count,
            suspended_rate=suspended_count / n if n else 0.0,
            model_version_counts=model_version_counts,
        ),
        model=model_summary,
    )


@app.get("/matches", response_model=MatchListResponse)
def list_matches(tournament: str | None = None, surface: str | None = None) -> MatchListResponse:
    """Browse replayable matches (i.e. matches with points loaded), the
    scenario-library/filters part of Journey 6. Filters are exact,
    case-insensitive matches - no fuzzy search yet."""
    matches = repository.list_matches()
    if tournament:
        matches = [m for m in matches if m.tournament.lower() == tournament.lower()]
    if surface:
        matches = [m for m in matches if m.surface.lower() == surface.lower()]
    matches.sort(key=lambda m: m.match_date, reverse=True)
    summaries = [_match_summary(m, repository) for m in matches]
    return MatchListResponse(matches=summaries, total=len(summaries))


@app.get("/replay/{match_id}", response_model=ReplayResponse)
def get_replay(match_id: str) -> ReplayResponse:
    match = repository.get_match(match_id)
    if match is None:
        raise HTTPException(status_code=404, detail=f"No match found for {match_id!r}")

    points = repository.get_points(match_id)
    outcome = repository.get_outcome(match_id)

    return ReplayResponse(
        match=_match_summary(match, repository),
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
    started_at = time.perf_counter()
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
    break_point = compute_break_point(points, point)
    points_a, points_b = game_score_before(points, point)
    p_a_serve, p_b_serve = _serve_rates_for(match)
    points_so_far = [p for p in points if p.point_no < point.point_no]

    pricing_result = compute_probability(
        artefacts=_artefacts,
        match=match,
        points_so_far=points_so_far,
        context=_context_cache.get(match.match_id, {}),
        p_a_serve_rate=p_a_serve,
        p_b_serve_rate=p_b_serve,
        sets_won_a=point.sets_won_a,
        sets_won_b=point.sets_won_b,
        games_won_a=point.games_won_a,
        games_won_b=point.games_won_b,
        server=point.server,
        points_a=points_a,
        points_b=points_b,
    )
    margin = WIDENED_MARGIN if pricing_result.widen_margin else DEFAULT_MARGIN
    trading_result = apply_trading_rules(pricing_result.probability_a, margin=margin)

    response = ProbabilityResponse(
        probability_request_id=f"req_{next(_request_ids):x}",
        match_id=request.match_id,
        point_sequence=request.point_sequence,
        interpretation=MatchStateInterpretation(
            set=point.set_no,
            games=f"{point.games_won_a}-{point.games_won_b}",
            server=point.server,
            break_point=break_point,
        ),
        probability_player_a=None if trading_result.suspended else pricing_result.probability_a,
        price_player_a=trading_result.price_a,
        price_player_b=trading_result.price_b,
        model_version=pricing_result.model_version,
        fallback_used=pricing_result.fallback_used,
        suspended=trading_result.suspended,
        markov_probability_a=pricing_result.markov_probability_a,
        ml_probability_a=pricing_result.ml_probability_a,
    )
    latency_ms = (time.perf_counter() - started_at) * 1000
    log_quote(response, latency_ms=latency_ms)
    return response


@app.post("/probability/preview", response_model=ProbabilityPreviewResponse)
def post_probability_preview(request: ProbabilityPreviewRequest) -> ProbabilityPreviewResponse:
    """Scores a hypothetical score state through the same pipeline
    `/probability` uses, without needing a real match in the repository.
    Used by the frontend's scripted scenario-library demo matches
    (frontend/src/lib/scoring.ts) so their probabilities are genuine
    model output - not a fabricated placeholder heuristic - while still
    letting the frontend script specific narrative beats (a suspension,
    a stale quote) that a historical replay has no way to reproduce on
    its own. Never logged to the quote event log: this isn't a real
    served quote, and mixing it into Journey 19's ops dashboard would
    misrepresent real production traffic with demo-page noise."""
    preview_match = Match(
        match_id="preview",
        tournament="",
        round="",
        surface="hard",
        best_of=request.best_of,
        match_date=date.today(),
        player_a_id="preview_a",
        player_b_id="preview_b",
        source="preview",
    )
    pricing_result = compute_probability(
        artefacts=_artefacts,
        match=preview_match,
        points_so_far=[],
        context={},
        p_a_serve_rate=request.p_a_serve_rate,
        p_b_serve_rate=request.p_b_serve_rate,
        sets_won_a=request.sets_a,
        sets_won_b=request.sets_b,
        games_won_a=request.games_a,
        games_won_b=request.games_b,
        server=request.server,
        points_a=request.points_a,
        points_b=request.points_b,
    )
    margin = WIDENED_MARGIN if pricing_result.widen_margin else DEFAULT_MARGIN
    trading_result = apply_trading_rules(pricing_result.probability_a, margin=margin)

    return ProbabilityPreviewResponse(
        probability_player_a=None if trading_result.suspended else pricing_result.probability_a,
        price_player_a=trading_result.price_a,
        price_player_b=trading_result.price_b,
        model_version=pricing_result.model_version,
        fallback_used=pricing_result.fallback_used,
        suspended=trading_result.suspended,
        markov_probability_a=pricing_result.markov_probability_a,
        ml_probability_a=pricing_result.ml_probability_a,
    )
