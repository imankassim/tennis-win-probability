import pytest

from pricing.registry import RegistryEntry, active_version, add_entry, load_registry, set_active_version


def _entry(version, active=True):
    return RegistryEntry(
        version=version,
        model_version="blend_v1_calibrated",
        trained_at="2026-01-01T00:00:00+00:00",
        n_training_matches=100,
        n_calibration_matches=10,
        calibration_brier=0.15,
        calibration_log_loss=0.45,
        calibration_ece=0.02,
        active=active,
    )


def test_load_registry_returns_empty_list_when_nothing_promoted_yet(tmp_path):
    assert load_registry(tmp_path) == []


def test_add_entry_persists_and_is_readable(tmp_path):
    add_entry(tmp_path, _entry("v1"))
    entries = load_registry(tmp_path)
    assert len(entries) == 1
    assert entries[0].version == "v1"
    assert entries[0].active is True


def test_add_entry_marks_only_the_newest_version_active(tmp_path):
    add_entry(tmp_path, _entry("v1"))
    add_entry(tmp_path, _entry("v2"))
    entries = {e.version: e for e in load_registry(tmp_path)}
    assert entries["v1"].active is False
    assert entries["v2"].active is True


def test_active_version_returns_none_when_registry_is_empty(tmp_path):
    assert active_version(tmp_path) is None


def test_active_version_returns_the_active_entry(tmp_path):
    add_entry(tmp_path, _entry("v1"))
    add_entry(tmp_path, _entry("v2"))
    assert active_version(tmp_path).version == "v2"


def test_set_active_version_can_roll_back_to_an_older_version(tmp_path):
    add_entry(tmp_path, _entry("v1"))
    add_entry(tmp_path, _entry("v2"))
    set_active_version(tmp_path, "v1")

    entries = {e.version: e for e in load_registry(tmp_path)}
    assert entries["v1"].active is True
    assert entries["v2"].active is False
    assert active_version(tmp_path).version == "v1"


def test_set_active_version_raises_for_an_unknown_version(tmp_path):
    add_entry(tmp_path, _entry("v1"))
    with pytest.raises(ValueError, match="v99"):
        set_active_version(tmp_path, "v99")
