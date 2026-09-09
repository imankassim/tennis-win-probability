"""Sync test (Journey 18): asserts the live `/probability` feature path
(backend/probability.py's build_feature_row) computes exactly the same
feature values as the offline training path
(pricing/ml/features.py's build_point_features) for the same point.

These are two independent implementations - the offline path builds a
whole training frame in one pass, the live path scores one point at a
time from cached per-match context - kept in sync only by convention
(matching constants, matching arithmetic), not by sharing a single
function. Without a test like this, someone could edit one side's
momentum window or context default and silently create training/serving
skew, a real and well-known ML reliability failure mode, undetectable
from either side in isolation.
"""

from datetime import date, timedelta

import pytest

from backend.probability import build_feature_row
from database.models import Match, OutcomeLabel, Point
from pricing.ml.features import build_point_features, compute_match_context_features
from pricing.ml.train import FEATURE_SETS

A, B, C = "player_a_id", "player_b_id", "player_c_id"
FEATURE_COLUMNS = FEATURE_SETS["state_context_momentum"]


def _match(match_id, d, p1, p2, best_of=3):
    return Match(
        match_id=match_id,
        tournament="t",
        round="F",
        surface="hard",
        best_of=best_of,
        match_date=d,
        player_a_id=p1,
        player_b_id=p2,
        source="test",
    )


def _point(match_id, point_no, server, winner, sa, sb, ga, gb):
    return Point(
        match_id=match_id,
        point_no=point_no,
        set_no=1,
        game_no=1,
        server=server,
        point_winner=winner,
        sets_won_a=sa,
        sets_won_b=sb,
        games_won_a=ga,
        games_won_b=gb,
        point_score="n/a",
    )


def _archive():
    """Three matches so the third has real (non-default) context: prior
    form, a surface record and a head-to-head history to draw on - a
    debut-only archive would let every context feature pass this test
    trivially at its neutral default."""
    base = date(2026, 1, 1)
    matches = [
        _match("m1", base, A, B),
        _match("m2", base + timedelta(days=5), A, C),
        _match("m3", base + timedelta(days=10), A, B),
    ]
    outcomes = {
        "m1": OutcomeLabel(match_id="m1", actual_winner="player_a", final_score="2-0"),
        "m2": OutcomeLabel(match_id="m2", actual_winner="player_b", final_score="2-1"),
        "m3": OutcomeLabel(match_id="m3", actual_winner="player_a", final_score="2-1"),
    }
    points_by_match = {
        "m1": [
            _point("m1", 1, "player_a", "player_a", 0, 0, 0, 0),
            _point("m1", 2, "player_a", "player_a", 0, 0, 0, 0),
        ],
        "m2": [
            _point("m2", 1, "player_b", "player_b", 0, 0, 0, 0),
        ],
        "m3": [
            _point("m3", 1, "player_a", "player_a", 0, 0, 0, 0),
            _point("m3", 2, "player_b", "player_b", 0, 0, 1, 0),
            _point("m3", 3, "player_b", "player_a", 1, 0, 1, 0),
            _point("m3", 4, "player_a", "player_b", 1, 0, 1, 1),
        ],
    }
    return matches, points_by_match, outcomes


def test_live_feature_row_matches_offline_training_row_for_every_point():
    matches, points_by_match, outcomes = _archive()
    matches_by_id = {m.match_id: m for m in matches}
    ctx = compute_match_context_features(matches, outcomes)
    offline_df = build_point_features(matches, points_by_match, outcomes, ctx)

    for match_id, points in points_by_match.items():
        match = matches_by_id[match_id]
        match_context = ctx.get(match_id, {})
        for i, point in enumerate(points):
            offline_row = offline_df[
                (offline_df["match_id"] == match_id) & (offline_df["point_no"] == point.point_no)
            ].iloc[0]

            live_row = build_feature_row(
                match=match,
                points_so_far=points[:i],
                context=match_context,
                sets_won_a=point.sets_won_a,
                sets_won_b=point.sets_won_b,
                games_won_a=point.games_won_a,
                games_won_b=point.games_won_b,
                server=point.server,
            )

            for feature in FEATURE_COLUMNS:
                assert live_row[feature] == pytest.approx(offline_row[feature]), (
                    f"{match_id} point {point.point_no}: {feature} live={live_row[feature]!r} "
                    f"offline={offline_row[feature]!r}"
                )

