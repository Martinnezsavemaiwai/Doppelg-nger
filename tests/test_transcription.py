import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from thai_voice_clone.config import Settings
from thai_voice_clone.transcription import (
    WORKER_RESULT_PREFIX,
    LocalWhisperTranscriber,
    SubprocessWhisperTranscriber,
    TranscriptionError,
)


def test_subprocess_transcriber_uses_isolated_worker_and_parses_result(
    tmp_path, monkeypatch
):
    source = tmp_path / "เสียง sample.webm"
    source.write_bytes(b"webm")
    settings = SimpleNamespace(device_mode="cpu")
    calls = []

    monkeypatch.setenv("THAI_VOICE_WHISPER_MODEL", "tiny")

    def runner(command, **kwargs):
        calls.append((command, kwargs))
        payload = {
            "text": "สวัสดีครับ",
            "duration": 2.5,
            "language": "th",
        }
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=WORKER_RESULT_PREFIX + json.dumps(payload, ensure_ascii=False),
            stderr="",
        )

    result = SubprocessWhisperTranscriber(settings, runner=runner).transcribe(source)

    assert result.text == "สวัสดีครับ"
    assert result.duration == 2.5
    assert result.language == "th"
    assert calls[0][0][:3] == [
        sys.executable,
        "-m",
        "thai_voice_clone.transcription_worker",
    ]
    assert Path(calls[0][0][3]) == source
    assert calls[0][1]["capture_output"] is True
    assert calls[0][1]["text"] is True
    assert calls[0][1]["env"]["THAI_VOICE_WHISPER_MODEL"] == "tiny"


def test_subprocess_transcriber_normalizes_worker_timeout(tmp_path):
    source = tmp_path / "voice.wav"
    source.write_bytes(b"wav")
    settings = SimpleNamespace(device_mode="cpu")

    def runner(command, **kwargs):
        raise subprocess.TimeoutExpired(command, timeout=30)

    transcriber = SubprocessWhisperTranscriber(settings, runner=runner)
    with pytest.raises(TranscriptionError, match="กรอกข้อความเอง"):
        transcriber.transcribe(source)


def test_subprocess_transcriber_normalizes_malformed_worker_output(tmp_path):
    source = tmp_path / "voice.wav"
    source.write_bytes(b"wav")
    settings = SimpleNamespace(device_mode="cpu")

    def runner(command, **kwargs):
        return subprocess.CompletedProcess(command, 0, stdout="not-json", stderr="")

    transcriber = SubprocessWhisperTranscriber(settings, runner=runner)
    with pytest.raises(TranscriptionError, match="กรอกข้อความเอง"):
        transcriber.transcribe(source)


@pytest.mark.parametrize("stdout_encoding", [None, "cp874"])
def test_worker_emits_utf8_thai_under_a_non_utf8_windows_locale(
    tmp_path, stdout_encoding
):
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in {"PYTHONUTF8", "PYTHONIOENCODING"}
    }
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
    if stdout_encoding:
        env["PYTHONIOENCODING"] = stdout_encoding

    completed = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8=0",
            "-m",
            "thai_voice_clone.transcription_worker",
            str(tmp_path / "missing.wav"),
        ],
        capture_output=True,
        env=env,
    )

    assert completed.stdout.decode("utf-8").startswith(WORKER_RESULT_PREFIX)
    assert "ไม่พบไฟล์เสียง" in completed.stdout.decode("utf-8")


def test_subprocess_transcriber_survives_undecodable_worker_output(tmp_path):
    source = tmp_path / "voice.wav"
    source.write_bytes(b"wav")

    def runner(command, **kwargs):
        script = "import sys; sys.stdout.buffer.write(b'\\xca\\xc7\\n')"
        return subprocess.run([sys.executable, "-c", script], **kwargs)

    transcriber = SubprocessWhisperTranscriber(SimpleNamespace(), runner=runner)
    with pytest.raises(TranscriptionError, match="กรอกข้อความเอง"):
        transcriber.transcribe(source)


def test_transcriber_joins_segments_and_reuses_model(tmp_path, monkeypatch):
    source = tmp_path / "voice.webm"
    source.write_bytes(b"webm")
    settings = Settings(root=tmp_path, device_mode="cpu")
    monkeypatch.setenv("THAI_VOICE_WHISPER_MODEL", "tiny")
    created = []

    class FakeModel:
        def transcribe(self, path, **kwargs):
            assert path == str(source)
            assert kwargs["language"] == "th"
            return iter(
                [
                    SimpleNamespace(text=" สวัสดี"),
                    SimpleNamespace(text="ครับ วันนี้"),
                ]
            ), SimpleNamespace(duration=6.5, language="th")

    def factory(model_name, device, compute_type):
        created.append((model_name, device, compute_type))
        return FakeModel()

    transcriber = LocalWhisperTranscriber(settings, model_factory=factory)
    first = transcriber.transcribe(source)
    second = transcriber.transcribe(source)

    assert first.text == "สวัสดี ครับ วันนี้"
    assert first.duration == 6.5
    assert first.language == "th"
    assert second == first
    assert created == [("tiny", "cpu", "int8")]


def test_transcriber_reports_missing_dependency_as_user_error(tmp_path):
    source = tmp_path / "voice.wav"
    source.write_bytes(b"wav")
    settings = Settings(root=tmp_path, device_mode="cpu")

    def missing_dependency(*_args):
        raise ImportError("faster-whisper is not installed")

    transcriber = LocalWhisperTranscriber(settings, model_factory=missing_dependency)
    with pytest.raises(TranscriptionError, match="faster-whisper"):
        transcriber.transcribe(source)
