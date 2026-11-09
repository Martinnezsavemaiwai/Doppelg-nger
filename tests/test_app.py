from contextlib import contextmanager
from pathlib import Path

import pytest

from thai_voice_clone.app import build_app, generate
from thai_voice_clone.validation import UserInputError


class FakeService:
    def __init__(self):
        self.calls = []

    def synthesize(self, request, reference, output):
        self.calls.append((request, reference, output))
        Path(output).write_bytes(b"RIFFvalid")
        return Path(output)


def test_generate_validates_prepares_and_returns_result_paths(tmp_path):
    source = tmp_path / "voice.wav"
    source.write_bytes(b"RIFF")
    normalized = tmp_path / "normalized.wav"
    normalized.write_bytes(b"RIFF")

    @contextmanager
    def prepare(_):
        yield normalized

    service = FakeService()
    output = tmp_path / "result.wav"
    status, player, download = generate(
        source,
        "ต้นฉบับ",
        "ข้อความใหม่",
        "v1",
        1.0,
        duration_probe=lambda _: 6.0,
        prepare=prepare,
        service=service,
        output_factory=lambda: output,
    )
    assert status == "สร้างเสียงเรียบร้อย"
    assert player == download == str(output)
    assert service.calls[0][1] == normalized


def test_generate_keeps_reference_warning_in_success_status(tmp_path):
    source = tmp_path / "voice.wav"
    source.write_bytes(b"RIFF")

    @contextmanager
    def prepare(path):
        yield path

    status, _, _ = generate(
        source,
        "ต้นฉบับ",
        "ใหม่",
        "v1",
        1.0,
        lambda _: 10.0,
        prepare,
        FakeService(),
        lambda: tmp_path / "out.wav",
    )
    assert "4 ถึง 8" in status


def test_generate_rejects_missing_reference_before_running_ffprobe(tmp_path):
    with pytest.raises(UserInputError, match="เลือกไฟล์เสียง"):
        generate(
            None,
            "ต้นฉบับ",
            "ใหม่",
            "v1",
            1.0,
            duration_probe=lambda _: pytest.fail("ffprobe should not run"),
            prepare=lambda _: pytest.fail("conversion should not run"),
            service=FakeService(),
            output_factory=lambda: tmp_path / "out.wav",
        )


def test_build_app_does_not_load_model():
    gr = pytest.importorskip("gradio")
    app = build_app(service_factory=lambda settings: (_ for _ in ()).throw(AssertionError()))
    assert isinstance(app, gr.Blocks)
