from pathlib import Path
from dataclasses import replace
import sys
from types import SimpleNamespace

import pytest

from thai_voice_clone.model import (
    ModelError,
    VoiceCloneService,
    create_f5_backend,
    select_device,
    split_generation_text,
)
from thai_voice_clone.validation import GenerationRequest


def request(tmp_path, model="v1"):
    return GenerationRequest(
        tmp_path / "ref.wav", "ต้นฉบับ", "ข้อความใหม่", model, 1.0
    )


@pytest.mark.parametrize(
    "mode,available,expected",
    [
        ("cpu", True, "cpu"),
        ("auto", False, "cpu"),
        ("auto", True, "cuda"),
        ("cuda", True, "cuda"),
    ],
)
def test_select_device_modes(mode, available, expected):
    assert select_device(mode, lambda: available, lambda: None) == expected


def test_forced_cuda_fails_when_unavailable():
    with pytest.raises(ModelError, match="CUDA"):
        select_device("cuda", lambda: False, lambda: None)


def test_auto_falls_back_when_cuda_probe_breaks():
    def broken():
        raise RuntimeError("allocation failed")

    assert select_device("auto", lambda: True, broken) == "cpu"


def test_forced_cuda_reports_failed_probe():
    def broken():
        raise RuntimeError("allocation failed")

    with pytest.raises(ModelError, match="CUDA เริ่มทำงาน"):
        select_device("cuda", lambda: True, broken)


def test_service_caches_backend_and_writes_24khz_wave(tmp_path):
    created = []
    written = []

    class FakeBackend:
        def infer(self, **kwargs):
            assert kwargs["step"] == 32
            assert kwargs["max_chars"] == 100
            return [0.0, 0.1, -0.1]

    def factory(model, device):
        created.append((model, device))
        return FakeBackend()

    def writer(path, waveform, sample_rate):
        written.append((list(waveform), sample_rate))
        Path(path).write_bytes(b"RIFFvalid")

    service = VoiceCloneService("cpu", factory, writer, lambda path: True)
    reference = tmp_path / "normalized.wav"
    reference.write_bytes(b"RIFF")
    for name in ("one.wav", "two.wav"):
        service.synthesize(request(tmp_path), reference, tmp_path / name)
    assert created == [("v1", "cpu")]
    assert written == [([0.0, 0.1, -0.1], 24000)] * 2


def test_split_generation_text_turns_punctuation_into_pause_metadata():
    assert split_generation_text("สวัสดีครับ, วันนี้เป็นอย่างไรบ้าง?") == [
        ("สวัสดีครับ", 0.16),
        ("วันนี้เป็นอย่างไรบ้าง", 0.32),
    ]


@pytest.mark.parametrize(
    "text,expected",
    [
        ("ราคา 1,000 บาท", "ราคา 1000 บาท"),
        ("ยอด 1,250,000 บาท", "ยอด 1250000 บาท"),
        ("เวอร์ชัน 3.14 ออกแล้ว", "เวอร์ชัน 3 จุด 1 4 ออกแล้ว"),
        ("พ.ศ. 2567 ที่ผ่านมา", "พศ 2567 ที่ผ่านมา"),
        ("คุณ น.ส.สมศรี มาแล้ว", "คุณ นส สมศรี มาแล้ว"),
        ("กรุงเทพฯ เป็นเมืองหลวง", "กรุงเทพฯ เป็นเมืองหลวง"),
        ("ผัก ผลไม้ ฯลฯ ขายหมด", "ผัก ผลไม้ ฯลฯ ขายหมด"),
    ],
)
def test_split_keeps_numbers_and_abbreviations_in_one_clause(text, expected):
    assert split_generation_text(text) == [(expected, 0.0)]


def test_split_still_breaks_after_a_number_that_ends_a_sentence():
    assert split_generation_text("ราคา 1,000. ถูกมาก") == [
        ("ราคา 1000", 0.32),
        ("ถูกมาก", 0.0),
    ]


@pytest.mark.parametrize("device,cuda_seen", [("cpu", False), ("cuda", True)])
def test_f5_backend_imports_with_the_selected_device(monkeypatch, device, cuda_seen):
    torch = SimpleNamespace(cuda=SimpleNamespace(is_available=lambda: True))

    class FakeTTS:
        def __init__(self, model):
            self.cuda_seen = torch.cuda.is_available()

    monkeypatch.setitem(sys.modules, "torch", torch)
    monkeypatch.setitem(sys.modules, "f5_tts_th", SimpleNamespace())
    monkeypatch.setitem(sys.modules, "f5_tts_th.tts", SimpleNamespace(TTS=FakeTTS))

    assert create_f5_backend("v1", device).cuda_seen is cuda_seen


def test_service_inserts_natural_pauses_between_sentence_segments(tmp_path):
    calls = []

    class FakeBackend:
        def infer(self, **kwargs):
            calls.append(kwargs)
            return [0.0, 0.1]

    def writer(path, waveform, sample_rate):
        assert sample_rate == 24000
        assert len(waveform) == 7684
        Path(path).write_bytes(b"RIFFvalid")

    service = VoiceCloneService("cpu", lambda *_: FakeBackend(), writer, lambda _: True)
    output = tmp_path / "out.wav"
    service.synthesize(
        replace(request(tmp_path), text="ประโยคแรก. ประโยคที่สอง"),
        tmp_path / "ref.wav",
        output,
    )

    assert len(calls) == 2


def test_service_preserves_punctuation_segments_for_generation(tmp_path):
    calls = []

    class FakeBackend:
        def infer(self, **kwargs):
            calls.append(kwargs)
            return [0.0]

    def writer(path, waveform, sample_rate):
        Path(path).write_bytes(b"RIFFvalid")

    service = VoiceCloneService("cpu", lambda *_: FakeBackend(), writer, lambda _: True)
    service.synthesize(
        replace(request(tmp_path), text="ประโยคแรก. ประโยคที่สอง"),
        tmp_path / "ref.wav",
        tmp_path / "out.wav",
    )

    assert [call["gen_text"] for call in calls] == ["ประโยคแรก", "ประโยคที่สอง"]
    assert all(call["ref_text"] == "ต้นฉบับ" for call in calls)


def test_service_rejects_empty_or_unreadable_output(tmp_path):
    class FakeBackend:
        def infer(self, **kwargs):
            return []

    def writer(path, waveform, sample_rate):
        Path(path).write_bytes(b"")

    service = VoiceCloneService(
        "cpu", lambda *_: FakeBackend(), writer, lambda path: False
    )
    with pytest.raises(ModelError, match="ไฟล์เสียงผลลัพธ์"):
        service.synthesize(request(tmp_path), tmp_path / "ref.wav", tmp_path / "out.wav")


def test_service_translates_out_of_memory_and_removes_partial_output(tmp_path):
    output = tmp_path / "partial.wav"

    class FakeBackend:
        def infer(self, **kwargs):
            output.write_bytes(b"partial")
            raise RuntimeError("CUDA out of memory")

    service = VoiceCloneService(
        "cuda", lambda *_: FakeBackend(), lambda *args: None, lambda path: True
    )
    with pytest.raises(ModelError, match="หน่วยความจำการ์ดจอ"):
        service.synthesize(request(tmp_path), tmp_path / "ref.wav", output)
    assert not output.exists()
