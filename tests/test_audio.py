from pathlib import Path
from types import SimpleNamespace

import pytest

from thai_voice_clone.audio import AudioPreparationError, prepared_reference, probe_duration


def test_probe_duration_uses_ffprobe_machine_output(tmp_path):
    source = tmp_path / "voice.mp3"
    source.write_bytes(b"x")
    calls = []

    def runner(args, **kwargs):
        calls.append((args, kwargs))
        return SimpleNamespace(returncode=0, stdout="6.25\n", stderr="")

    assert probe_duration(source, runner) == 6.25
    assert calls[0][0][0] == "ffprobe"
    assert calls[0][0][-1] == str(source)
    assert calls[0][1]["shell"] is False


def test_probe_rejects_corrupt_audio(tmp_path):
    source = tmp_path / "bad.wav"
    source.write_bytes(b"bad")

    def runner(*args, **kwargs):
        return SimpleNamespace(returncode=1, stdout="", stderr="invalid data")

    with pytest.raises(AudioPreparationError, match="อ่านไฟล์เสียงไม่ได้"):
        probe_duration(source, runner)


def test_prepared_reference_builds_safe_ffmpeg_call_and_cleans_up(tmp_path):
    source = tmp_path / "name & unsafe.mp3"
    source.write_bytes(b"x")
    calls = []

    def runner(args, **kwargs):
        calls.append(args)
        Path(args[-1]).write_bytes(b"RIFFvalid")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    with prepared_reference(source, runner) as normalized:
        assert normalized.exists()
        assert normalized.suffix == ".wav"
        assert calls[0][:2] == ["ffmpeg", "-nostdin"]
        assert calls[0][calls[0].index("-ar") + 1] == "24000"
        temp_parent = normalized.parent
    assert not temp_parent.exists()


def missing_executable(*args, **kwargs):
    raise FileNotFoundError("ffmpeg")


def test_probe_reports_missing_ffmpeg_as_audio_error(tmp_path):
    with pytest.raises(AudioPreparationError, match="FFmpeg"):
        probe_duration(tmp_path / "voice.wav", missing_executable)


def test_prepared_reference_reports_missing_ffmpeg_as_audio_error(tmp_path):
    with pytest.raises(AudioPreparationError, match="FFmpeg"):
        with prepared_reference(tmp_path / "voice.wav", missing_executable):
            pass


def test_prepared_reference_cleans_up_when_ffmpeg_fails(tmp_path):
    source = tmp_path / "bad.mp3"
    source.write_bytes(b"x")

    def runner(*args, **kwargs):
        return SimpleNamespace(returncode=1, stdout="", stderr="failed")

    with pytest.raises(AudioPreparationError, match="แปลงไฟล์เสียงไม่สำเร็จ"):
        with prepared_reference(source, runner):
            pass
