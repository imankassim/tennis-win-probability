"""CLI entry point for pricing/promote_model.py.

Kept in a separate module deliberately: running `python -m
pricing.promote_model` directly would load that module as `__main__`
rather than `pricing.promote_model`, and joblib/pickle identifies a class
by the module it's reachable from in `sys.modules` - a `PricingArtefacts`
pickled while its own defining module was loaded as `__main__` cannot be
unpickled later by a normal `import pricing.promote_model` (e.g.
backend/main.py at startup), because that import never registers the
class under the `__main__` name pickle recorded. Importing
pricing.promote_model normally from here, instead of executing it
directly, avoids the problem entirely.

Usage:
    python -m pricing.run_promotion <matches.csv> <points1.csv> [<points2.csv> ...]
"""

from __future__ import annotations

import sys
from pathlib import Path

from pricing.promote_model import (
    ARTEFACT_FILENAME,
    DEFAULT_ARTEFACT_DIR,
    save_artefacts,
    train_and_promote,
)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        raise SystemExit(1)
    result = train_and_promote(Path(sys.argv[1]), [Path(p) for p in sys.argv[2:]])
    save_artefacts(result)
    print(f"Promoted {result.model_version}")
    print(f"  ML model trained on {result.n_training_matches} matches")
    print(f"  Calibrator fit on {result.n_calibration_matches} held-out matches")
    print(f"  Saved to {DEFAULT_ARTEFACT_DIR / ARTEFACT_FILENAME}")
