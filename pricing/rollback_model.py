"""CLI for rolling back the served pricing pipeline to a previously
promoted version (Journey 20's "rollback target" — the model registry
component the source document names explicitly).

Every promotion (pricing/promote_model.py) keeps its artefact file under
docs/model_cards/artefacts/versions/ rather than overwriting it, and
records itself in the registry (pricing/registry.py) — so rolling back
is just: copy an older version's file back over the fixed active
filename backend/probability.py's load_artefacts reads, and mark that
version active in the registry. No retraining, no new evidence — this is
an operations action, not a promotion decision, but it's still a
deliberate one a person runs on purpose (never automatic), matching
docs/architecture/governance.md's "require review for model promotion"
— a rollback changes what's served exactly the same way a promotion
does.

Usage:
    python -m pricing.rollback_model --list
    python -m pricing.rollback_model <version>
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from pricing.promote_model import ARTEFACT_FILENAME, DEFAULT_ARTEFACT_DIR, VERSIONS_SUBDIR
from pricing.registry import load_registry, set_active_version


def list_versions(directory: Path = DEFAULT_ARTEFACT_DIR) -> None:
    entries = load_registry(directory)
    if not entries:
        print(f"No promoted versions found in {directory}.")
        return
    for entry in entries:
        marker = "* " if entry.active else "  "
        print(
            f"{marker}{entry.version}  {entry.model_version}  "
            f"brier={entry.calibration_brier:.4f}  ece={entry.calibration_ece:.4f}  "
            f"trained_at={entry.trained_at}"
        )


def rollback_to(version: str, directory: Path = DEFAULT_ARTEFACT_DIR) -> None:
    """Raises ValueError (via set_active_version) if `version` isn't a
    known registry entry, or FileNotFoundError if its artefact file is
    somehow missing — either way, before touching the currently-active
    file, so a bad rollback request never leaves the active artefact
    half-replaced."""
    versioned_path = directory / VERSIONS_SUBDIR / f"pricing_pipeline_{version}.joblib"
    if not versioned_path.exists():
        raise FileNotFoundError(f"no artefact file found for version {version!r}: {versioned_path}")

    set_active_version(directory, version)  # validates the version is registered
    shutil.copyfile(versioned_path, directory / ARTEFACT_FILENAME)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        raise SystemExit(1)
    if sys.argv[1] == "--list":
        list_versions()
        raise SystemExit(0)
    rollback_to(sys.argv[1])
    print(f"Rolled back to version {sys.argv[1]}")
