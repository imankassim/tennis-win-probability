"""The model/configuration registry (Journey 20): every promoted pipeline
is kept, not overwritten, so a promotion can be rolled back to a known
prior version — the source document's own registry component ("Version -
data split - features - metrics - approval status - rollback target").

`pricing/promote_model.py` writes one entry here per promotion, alongside
the versioned artefact file it belongs to; `pricing/rollback_model.py`
reads it to list versions and to switch which one is active. Promotion
IS the human approval step (docs/architecture/governance.md's "require
review for model promotion") — every entry here was therefore reviewed
by whoever ran the promotion script; there is no separate unreviewed
state to track.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

REGISTRY_FILENAME = "registry.json"


@dataclass(frozen=True)
class RegistryEntry:
    version: str
    model_version: str
    trained_at: str
    n_training_matches: int
    n_calibration_matches: int
    calibration_brier: float
    calibration_log_loss: float
    calibration_ece: float
    active: bool


def _registry_path(directory: Path) -> Path:
    return directory / REGISTRY_FILENAME


def load_registry(directory: Path) -> list[RegistryEntry]:
    """Every promoted version on record, oldest first. Empty if nothing
    has ever been promoted on this checkout — not an error, the same
    "nothing here yet" case pricing/promote_model.py's artefact loading
    already treats as normal."""
    path = _registry_path(directory)
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return [RegistryEntry(**row) for row in json.load(f)]


def _save_registry(directory: Path, entries: list[RegistryEntry]) -> None:
    path = _registry_path(directory)
    path.write_text(json.dumps([asdict(e) for e in entries], indent=2), encoding="utf-8")


def add_entry(directory: Path, entry: RegistryEntry) -> None:
    """Records a newly promoted version as active, marking every earlier
    entry superseded — exactly one version is active at a time, matching
    there being exactly one file backend/probability.py's load_artefacts
    reads from."""
    entries = load_registry(directory)
    entries = [RegistryEntry(**{**asdict(e), "active": False}) for e in entries]
    entries.append(entry)
    _save_registry(directory, entries)


def set_active_version(directory: Path, version: str) -> RegistryEntry:
    """Marks `version` active and every other entry superseded — the
    rollback (or roll-forward) operation on the registry itself, separate
    from actually copying that version's artefact file into place
    (pricing/rollback_model.py does both together). Raises ValueError if
    `version` isn't a known entry, rather than silently doing nothing."""
    entries = load_registry(directory)
    if not any(e.version == version for e in entries):
        raise ValueError(f"no registry entry for version {version!r}")
    updated = [RegistryEntry(**{**asdict(e), "active": e.version == version}) for e in entries]
    _save_registry(directory, updated)
    return next(e for e in updated if e.version == version)


def active_version(directory: Path) -> RegistryEntry | None:
    for entry in load_registry(directory):
        if entry.active:
            return entry
    return None
