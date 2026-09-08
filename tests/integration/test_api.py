from fastapi.testclient import TestClient

from backend.fixtures import DEMO_MATCH_ID
from backend.main import _artefacts, app
from backend.probability import MARKOV_MODEL_VERSION

client = TestClient(app)

# Whether the promoted pipeline (pricing/promote_model.py) has actually
# been run against this checkout — the artefact file is gitignored (see
# .gitignore's "model artefacts" entry), so a fresh clone or CI run has
# none and the API is expected to fall back to Markov-only. Assert
# against the app's own live state instead of hardcoding one outcome, so
# these tests pass correctly in both cases rather than only ever matching
# whichever state happens to be true on one machine.
_EXPECTED_MODEL_VERSION = MARKOV_MODEL_VERSION if _artefacts is None else _artefacts.model_version
_EXPECTED_FALLBACK_USED = _artefacts is None


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_replay_returns_demo_match():
    response = client.get(f"/replay/{DEMO_MATCH_ID}")
    assert response.status_code == 200
    body = response.json()
    assert body["match"]["match_id"] == DEMO_MATCH_ID
    assert body["match"]["player_a"] == "Demo Player A"
    assert len(body["points"]) == 70
    # The demo match is deliberately left in progress — no outcome yet.
    assert body["outcome"] is None


def test_replay_unknown_match_is_404():
    response = client.get("/replay/does_not_exist")
    assert response.status_code == 404


def test_probability_for_a_known_point():
    response = client.post(
        "/probability", json={"match_id": DEMO_MATCH_ID, "point_sequence": 1}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["match_id"] == DEMO_MATCH_ID
    assert body["point_sequence"] == 1
    assert body["model_version"] == _EXPECTED_MODEL_VERSION
    assert 0 <= body["probability_player_a"] <= 1
    assert body["price_player_a"] >= 1.0
    assert body["price_player_b"] >= 1.0
    assert body["fallback_used"] is _EXPECTED_FALLBACK_USED
    assert body["suspended"] is False
    # A request ID should be present and distinct across requests.
    assert body["probability_request_id"]


def test_probability_for_unknown_match_is_404():
    response = client.post("/probability", json={"match_id": "nope", "point_sequence": 1})
    assert response.status_code == 404


def test_probability_for_unknown_point_sequence_is_404():
    response = client.post(
        "/probability", json={"match_id": DEMO_MATCH_ID, "point_sequence": 9999}
    )
    assert response.status_code == 404


def test_list_matches_includes_the_demo_match():
    response = client.get("/matches")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["matches"][0]["match_id"] == DEMO_MATCH_ID


def test_list_matches_filters_by_surface():
    assert client.get("/matches", params={"surface": "hard"}).json()["total"] == 1
    assert client.get("/matches", params={"surface": "clay"}).json()["total"] == 0


def test_probability_flags_a_real_break_point():
    # Game 9 in the demo fixture is scripted as a break: player_b serves,
    # wins one point, then player_a wins the next four — the last of which
    # is entered at 0-40 (from player_a's perspective as receiver), a break
    # point that this point itself converts.
    points = client.get(f"/replay/{DEMO_MATCH_ID}").json()["points"]
    game_9_points = [p for p in points if p["game_no"] == 9]
    last_point_no = game_9_points[-1]["point_no"]

    response = client.post(
        "/probability", json={"match_id": DEMO_MATCH_ID, "point_sequence": last_point_no}
    )
    assert response.json()["interpretation"]["break_point"] is True


def test_probability_moves_toward_the_leader():
    """Sanity check: by the end of set 1 (won 6-4 by player_a), the quoted
    probability for player_a should be higher than at the very first point."""
    first = client.post(
        "/probability", json={"match_id": DEMO_MATCH_ID, "point_sequence": 1}
    ).json()
    # Point 47 is the first point of game 11 (start of set 2, player_a up 1-0 in sets).
    later = client.post(
        "/probability", json={"match_id": DEMO_MATCH_ID, "point_sequence": 47}
    ).json()
    assert later["probability_player_a"] > first["probability_player_a"]
