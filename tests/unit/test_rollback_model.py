from dataclasses import replace

import joblib
import pytest

from database.models import Match, OutcomeLabel, Point
from pricing.promote_model import _train_and_promote_from_data, save_artefacts
from pricing.registry import load_registry
from pricing.rollback_model import rollback_to

PLAYERS = ["p1", "p2", "p3", "p4"]


def _tiny_artefacts():
    """A minimal but real PricingArtefacts, via the actual training path
    (not hand-built fakes) - this test cares about rollback's file/registry
    plumbing, not model quality, so a small archive is enough."""
    from datetime import date, timedelta
    import random

    rng = random.Random(0)
    matches, outcomes, points_by_match = [], {}, {}
    for m in range(30):
        match_id = f"m{m}"
        a, b = rng.sample(PLAYERS, 2)
        matches.append(
            Match(
                match_id=match_id, tournament="t", round="F", surface="hard", best_of=3,
                match_date=date(2024, 1, 1) + timedelta(days=m), player_a_id=a, player_b_id=b,
                source="test",
            )
        )
        a_wins = rng.random() > 0.5
        outcomes[match_id] = OutcomeLabel(
            match_id=match_id, actual_winner="player_a" if a_wins else "player_b", final_score="2-0"
        )
        points_by_match[match_id] = [
            Point(
                match_id=match_id, point_no=p + 1, set_no=1, game_no=1,
                server="player_a" if p % 2 == 0 else "player_b",
                point_winner="player_a" if a_wins else "player_b",
                sets_won_a=0, sets_won_b=0, games_won_a=0, games_won_b=0, point_score="n/a",
            )
            for p in range(10)
        ]
    return _train_and_promote_from_data(matches, points_by_match, outcomes)


def test_rollback_to_an_older_version_makes_it_the_active_artefact(tmp_path):
    artefacts = _tiny_artefacts()
    v1 = replace(artefacts, version="v1")
    v2 = replace(artefacts, version="v2")
    save_artefacts(v1, directory=tmp_path)
    save_artefacts(v2, directory=tmp_path)
    assert joblib.load(tmp_path / "pricing_pipeline.joblib").version == "v2"

    rollback_to("v1", directory=tmp_path)

    assert joblib.load(tmp_path / "pricing_pipeline.joblib").version == "v1"
    entries = {e.version: e for e in load_registry(tmp_path)}
    assert entries["v1"].active is True
    assert entries["v2"].active is False


def test_rollback_to_an_unknown_version_raises_without_touching_the_active_file(tmp_path):
    artefacts = _tiny_artefacts()
    v1 = replace(artefacts, version="v1")
    save_artefacts(v1, directory=tmp_path)

    with pytest.raises(FileNotFoundError):
        rollback_to("does-not-exist", directory=tmp_path)

    # The active artefact must be untouched by the failed rollback attempt.
    assert joblib.load(tmp_path / "pricing_pipeline.joblib").version == "v1"
    assert load_registry(tmp_path)[0].active is True
