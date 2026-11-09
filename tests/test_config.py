from datetime import datetime

import pytest

from thai_voice_clone.config import DEFAULT_SYNTHESIS_SPEED, load_settings


def test_default_synthesis_speed_favors_natural_pacing():
    assert DEFAULT_SYNTHESIS_SPEED == 0.8


def test_load_settings_defaults_to_auto_and_repository_paths(monkeypatch):
    monkeypatch.delenv("THAI_VOICE_DEVICE", raising=False)
    settings = load_settings()
    assert settings.device_mode == "auto"
    assert settings.output_dir.parts[-2:] == ("outputs", "generated")
    assert settings.default_reference.parts[-3:] == (
        "data",
        "reference",
        "user_voice.wav",
    )


def test_load_settings_rejects_unknown_device_mode(monkeypatch):
    monkeypatch.setenv("THAI_VOICE_DEVICE", "magic")
    with pytest.raises(ValueError, match="THAI_VOICE_DEVICE"):
        load_settings()


def test_new_output_path_is_contained_and_collision_resistant(tmp_path, monkeypatch):
    monkeypatch.setenv("THAI_VOICE_DEVICE", "cpu")
    settings = load_settings(root=tmp_path)
    path = settings.new_output_path(datetime(2026, 9, 20, 1, 2, 3), "abc123")
    assert path == (
        tmp_path / "outputs" / "generated" / "voice-20260920-010203-abc123.wav"
    )
    assert path.parent.resolve() == settings.output_dir.resolve()
