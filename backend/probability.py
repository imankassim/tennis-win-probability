"""Computes a probability for a given point in a match (Journey 17: the
online probability request sequence in
docs/architecture/logical-architecture.md, steps 5-8).

If a promoted pipeline exists (pricing/promote_model.py has been run,
producing docs/model_cards/artefacts/pricing_pipeline.joblib), computes
the Markov estimate and the ML estimate independently, blends them at the
promoted weight (EXP33), and applies the promoted phase calibrator
(EXP43) - `model_version` becomes the promoted bundle's own version
string (e.g. "blend_v1_calibrated"), `fallback_used=False`.

If no artefact exists - a fresh clone, or before anyone has run the
(deliberately manual, human-reviewed) promotion script - degrades to the
Markov engine alone, `model_version="markov_v1"`, `fallback_used=True`.
This is the graceful-degradation behaviour the architecture requires
(docs/architecture/logical-architecture.md's `fallback_used` flag), not
an error path.

Same degradation applies if the artefact exists but something in the
ML/blend/calibration path fails at request time (a corrupted file, an
incompatible scikit-learn/LightGBM version after an upgrade, a malformed
feature row) - the non-functional requirement this project's source
document states explicitly: "a failure in the ML, blend or calibration
layer must not prevent the Markov baseline from serving where it remains
available" (Journey 18, reliability). Two failure points are
distinguished, matching docs/architecture/deployment.md's fallback
table: if the ML model itself fails, this serves Markov-only with the
standard margin (the same as having no promoted artefact at all - a
routine degraded mode, not a red flag on its own); if the ML estimate
was obtained but blend or calibration then fails, this also serves
Markov-only but flags `widen_margin=True` for the caller to apply
trading_rules.WIDENED_MARGIN, since discarding a successfully-computed
ML estimate that disagreed with Markov (for reasons now unknown) carries
more genuine uncertainty than a routine Markov-only quote. See
tests/unit/test_probability_reliability.py for the failure-injection
tests covering both cases.

Pricing (margin, price bounds, suspension) is trading_rules/rules.py's
job, not this module's - this only returns the raw probability estimate.
"""

from __future__ import annotations

import warnings
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
# (e.g. no confirmed outcome yet) - the same neutral defaults
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
    # True only when a successfully-computed ML estimate had to be
    # discarded because blend or calibration then failed - see this
    # module's docstring. The caller (backend/main.py) uses this to pass
    # trading_rules.WIDENED_MARGIN instead of the default margin.
    widen_margin: bool = False
    # The Markov and ML estimates computed independently, before any
    # blend/calibration - surfaced so the API response (and the
    # dashboard's probability chart) can show the "math formula" and the
    # "learned model" as separate lines, not just their combined output.
    # Closes docs/ethics/assessment.md's recorded explainability gap
    # (the Markov/ML contribution split wasn't exposed in served
    # output). markov_probability_a is always available - the Markov
    # engine has no failure mode of its own. ml_probability_a is None
    # whenever no ML estimate was obtained at all (no promoted artefact,
    # or the ML model itself failed) - still populated if blend or
    # calibration failed AFTER a successful ML prediction, since that
    # number is real and worth showing even though it wasn't served.
    markov_probability_a: float = 0.0
    ml_probability_a: float | None = None


def load_artefacts(directory: Path = DEFAULT_ARTEFACT_DIR) -> PricingArtefacts | None:
    """The promoted pipeline (pricing/promote_model.py), if someone has
    run that script. None if no artefact file exists there, or if one
    exists but can't actually be loaded (a truncated/corrupted file from
    an interrupted write, or a pickle written by an incompatible library
    version) - a load failure degrades the same way a missing file does
    rather than crashing the whole API at startup (this is called once
    from a module-level global in backend/main.py), with a warning so the
    failure is still visible to whoever's operating the service."""
    path = directory / ARTEFACT_FILENAME
    if not path.exists():
        return None
    try:
        return joblib.load(path)
    except Exception as exc:  # noqa: BLE001 - any load failure degrades to Markov-only
        warnings.warn(f"Failed to load pricing artefacts from {path}: {exc}", stacklevel=2)
        return None


def _momentum_a(points_so_far: list[Point]) -> float:
    """Fraction of the last MOMENTUM_LOOKBACK points (within this match,
    strictly before the point being priced) won by player_a. Mirrors
    pricing/ml/features.py's `_momentum` exactly, so a live request scores
    the same feature the model was trained on."""
    if not points_so_far:
        return DEFAULT_FORM
    window = points_so_far[-MOMENTUM_LOOKBACK:]
    return sum(1 for p in window if p.point_winner == "player_a") / len(window)


def build_feature_row(
    match: Match,
    points_so_far: list[Point],
    context: dict[str, float],
    sets_won_a: int,
    sets_won_b: int,
    games_won_a: int,
    games_won_b: int,
    server: str,
) -> dict[str, float]:
    """The exact feature row a live `/probability` request scores -
    pulled out as its own function so a test can compare it directly
    against pricing/ml/features.py's `build_point_features` (the offline
    training path) for the same point, guarding against the two ever
    silently drifting apart (tests/unit/test_feature_sync.py, Journey
    18's "sync test"). `context` is this match's entry from the bulk
    context-feature cache (compute_match_context_features), or `{}` if
    the match has no confirmed outcome yet - missing keys fall back to
    _CONTEXT_DEFAULTS. `points_so_far` is this match's own points
    strictly before the one being priced (for the momentum feature)."""
    return {
        "best_of": match.best_of,
        "sets_a": sets_won_a,
        "sets_b": sets_won_b,
        "games_a": games_won_a,
        "games_b": games_won_b,
        "server_is_a": 1 if server == "player_a" else 0,
        "momentum_a": _momentum_a(points_so_far),
        **{feature: context.get(feature, _CONTEXT_DEFAULTS[feature]) for feature in CONTEXT_FEATURES},
    }


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
    confirmed outcome yet - missing keys fall back to _CONTEXT_DEFAULTS.
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
        return PricingResult(
            markov_p, MARKOV_MODEL_VERSION, fallback_used=True, markov_probability_a=markov_p
        )

    try:
        row = build_feature_row(
            match, points_so_far, context, sets_won_a, sets_won_b, games_won_a, games_won_b, server
        )
        x = pd.DataFrame([row])[artefacts.feature_columns]
        ml_p = float(artefacts.ml_model.predict_proba(x)[:, 1][0])
    except Exception as exc:  # noqa: BLE001 - the ML layer must never take Markov down with it
        warnings.warn(f"ML model failed, falling back to Markov: {exc}", stacklevel=2)
        return PricingResult(
            markov_p, MARKOV_MODEL_VERSION, fallback_used=True, markov_probability_a=markov_p
        )

    try:
        blended = blend_probability(markov_p, ml_p, artefacts.blend_markov_weight)
        phase = match_phase(sets_won_a + sets_won_b + 1, match.best_of)
        calibrated = artefacts.calibrator.predict([blended], [phase])[0]
    except Exception as exc:  # noqa: BLE001 - nor may the blend/calibration layer
        warnings.warn(
            f"Blend/calibration failed after a successful ML estimate, "
            f"falling back to Markov with a widened margin: {exc}",
            stacklevel=2,
        )
        return PricingResult(
            markov_p,
            MARKOV_MODEL_VERSION,
            fallback_used=True,
            widen_margin=True,
            markov_probability_a=markov_p,
            ml_probability_a=ml_p,
        )

    return PricingResult(
        calibrated,
        artefacts.model_version,
        fallback_used=False,
        markov_probability_a=markov_p,
        ml_probability_a=ml_p,
    )
