"""Computes a probability for a given point in a match (Journey 17: the
online probability request sequence in
docs/architecture/logical-architecture.md, steps 5-8).

If a promoted pipeline exists (pricing/promote_model.py has been run,
producing docs/model_cards/artefacts/pricing_pipeline.joblib), computes
the Markov estimate and the ML estimate independently, blends them at the
promoted weight (EXP33), and applies the promoted phase calibrator
(EXP43) — `model_version` becomes the promoted bundle's own version
string (e.g. "blend_v1_calibrated"), `fallback_used=False`.

If no artefact exists — a fresh clone, or before anyone has run the
(deliberately manual, human-reviewed) promotion script — degrades to the
Markov engine alone, `model_version="markov_v1"`, `fallback_used=True`.
This is the graceful-degradation behaviour the architecture requires
(docs/architecture/logical-architecture.md's `fallback_used` flag), not
an error path.

Pricing (margin, price bounds, suspension) is trading_rules/rules.py's
job, not this module's — this only returns the raw probability estimate.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import joblib
import pandas as pd

from backend.player_rating import DEFAULT_RATING
from database.models import Match, Point
from pricing.blend.blend import blend_probability
from pricing.calibration.calibration import match_phase
from pricing.markov.engine import markov_probability
from pricing.ml.features import CONTEXT_FEATURES, DEFAULT_FORM, MOMENTUM_LOOKBACK
from pricing.promote_model import ARTEFACT_FILENAME, DEFAULT_ARTEFACT_DIR, PricingArtefacts

MARKOV_MODEL_VERSION = "markov_v1"

# Every context feature the promoted model was trained on, and what to
# fall back to when a match has no entry in the context cache at all
# (e.g. no confirmed outcome yet) — the same neutral defaults
# compute_match_context_features itself uses for a debutant, so a
# missing cache entry behaves exactly like a player with no history.
_CONTEXT_DEFAULTS: dict[str, float] = {
    "form_a": DEFAULT_FORM,
    "form_b": DEFAULT_FORM,
    "surface_rate_a": DEFAULT_FORM,
    "surface_rate_b": DEFAULT_FORM,
    "h2h_rate_a": DEFAULT_FORM,
    "elo_a": DEFAULT_RATING,
    "elo_b": DEFAULT_RATING,
}


@dataclass(frozen=True)
class PricingResult:
    probability_a: float
    model_version: str
    fallback_used: bool


def load_artefacts(directory: Path = DEFAULT_ARTEFACT_DIR) -> PricingArtefacts | None:
    """The promoted pipeline (pricing/promote_model.py), if someone has
    run that script. None otherwise — callers degrade to Markov-only
    rather than treating this as an error, per this module's docstring."""
    path = directory / ARTEFACT_FILENAME
    if not path.exists():
        return None
    return joblib.load(path)


def _momentum_a(points_so_far: list[Point]) -> float:
    """Fraction of the last MOMENTUM_LOOKBACK points (within this match,
    strictly before the point being priced) won by player_a. Mirrors
    pricing/ml/features.py's `_momentum` exactly, so a live request scores
    the same feature the model was trained on."""
    if not points_so_far:
        return DEFAULT_FORM
    window = points_so_far[-MOMENTUM_LOOKBACK:]
    return sum(1 for p in window if p.point_winner == "player_a") / len(window)


def compute_probability(
    artefacts: PricingArtefacts | None,
    match: Match,
    points_so_far: list[Point],
    context: dict[str, float],
    p_a_serve_rate: float,
    p_b_serve_rate: float,
    sets_won_a: int,
    sets_won_b: int,
    games_won_a: int,
    games_won_b: int,
    server: str,
    points_a: int = 0,
    points_b: int = 0,
) -> PricingResult:
    """`context` is this match's entry from the bulk context-feature cache
    (compute_match_context_features), or `{}` if the match has no
    confirmed outcome yet — missing keys fall back to _CONTEXT_DEFAULTS.
    `points_so_far` is this match's own points strictly before the one
    being priced (for the within-match momentum feature)."""
    markov_p = markov_probability(
        p_a_serve_rate,
        p_b_serve_rate,
        match.best_of,
        sets_won_a,
        sets_won_b,
        games_won_a,
        games_won_b,
        server,
        points_a,
        points_b,
    )

    if artefacts is None:
        return PricingResult(markov_p, MARKOV_MODEL_VERSION, fallback_used=True)

    row = {
        "best_of": match.best_of,
        "sets_a": sets_won_a,
        "sets_b": sets_won_b,
        "games_a": games_won_a,
        "games_b": games_won_b,
        "server_is_a": 1 if server == "player_a" else 0,
        "momentum_a": _momentum_a(points_so_far),
        **{feature: context.get(feature, _CONTEXT_DEFAULTS[feature]) for feature in CONTEXT_FEATURES},
    }
    x = pd.DataFrame([row])[artefacts.feature_columns]
    ml_p = float(artefacts.ml_model.predict_proba(x)[:, 1][0])

    blended = blend_probability(markov_p, ml_p, artefacts.blend_markov_weight)
    phase = match_phase(sets_won_a + sets_won_b + 1, match.best_of)
    calibrated = artefacts.calibrator.predict([blended], [phase])[0]

    return PricingResult(calibrated, artefacts.model_version, fallback_used=False)
