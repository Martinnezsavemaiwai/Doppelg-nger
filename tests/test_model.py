from pathlib import Path
from dataclasses import replace
import sys
from types import SimpleNamespace

import pytest

from thai_voice_clone.model import (
    ModelError,
    VoiceCloneService,
    VoxCPMBackend,
    select_device,
    split_generation_text,
)
from thai_voice_clone.validation import GenerationRequest


def request(tmp_path):
    return GenerationRequest(tmp_path / "ref.wav", "ต้นฉบับ", "ข้อความใหม่")


class FakeBackend:
    sample_rate = 48000

    def __init__(self, waveform=(0.0, 0.1, -0.1), calls=None):
        self.waveform = list(waveform)
        self.calls = calls if calls is not None else []

    def infer(self, **kwargs):
        self.calls.append(kwargs)
        return self.waveform


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


def test_service_caches_backend_and_writes_at_backend_sample_rate(tmp_path):
    created = []
    written = []
    verified = []

    def factory(device):
        created.append(device)
        return FakeBackend()

    def writer(path, waveform, sample_rate):
        written.append((list(waveform), sample_rate))
        Path(path).write_bytes(b"RIFFvalid")

    def verifier(path, sample_rate):
        verified.append(sample_rate)
        return True

    service = VoiceCloneService("cpu", factory, writer, verifier)
    reference = tmp_path / "normalized.wav"
    reference.write_bytes(b"RIFF")
    for name in ("one.wav", "two.wav"):
        service.synthesize(request(tmp_path), reference, tmp_path / name)
    assert created == ["cpu"]
    assert written == [([0.0, 0.1, -0.1], 48000)] * 2
    assert verified == [48000, 48000]


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


def test_voxcpm_backend_loads_on_device_and_clones_with_reference(monkeypatch):
    loaded = {}
    generated = {}

    class FakeVoxCPM:
        tts_model = SimpleNamespace(sample_rate=48000)

        @classmethod
        def from_pretrained(cls, model_id, **kwargs):
            loaded.update(model_id=model_id, **kwargs)
            return cls()

        def generate(self, **kwargs):
            generated.update(kwargs)
            return [0.0]

    dtypes = []
    torch = SimpleNamespace(
        float32="float32",
        bfloat16="bfloat16",
        get_default_dtype=lambda: "float32",
        set_default_dtype=dtypes.append,
    )
    monkeypatch.setitem(sys.modules, "torch", torch)
    monkeypatch.setitem(sys.modules, "voxcpm", SimpleNamespace(VoxCPM=FakeVoxCPM))

    backend = VoxCPMBackend("cuda")
    assert backend.infer(ref_audio="ref.wav", ref_text="ต้นฉบับ", gen_text="ใหม่") == [0.0]
    assert backend.sample_rate == 48000
    assert loaded == {"model_id": "openbmb/VoxCPM2", "load_denoiser": False, "device": "cuda"}
    assert dtypes == ["bfloat16", "float32"]  # build in bf16, then restore the default
    assert generated["text"] == "ใหม่"
    assert generated["prompt_text"] == "ต้นฉบับ"
    assert generated["prompt_wav_path"] == generated["reference_wav_path"] == "ref.wav"


def test_service_inserts_natural_pauses_between_sentence_segments(tmp_path):
    calls = []

    def writer(path, waveform, sample_rate):
        assert sample_rate == 48000
        assert len(waveform) == 2 + round(0.32 * 48000) + 2
        Path(path).write_bytes(b"RIFFvalid")

    service = VoiceCloneService(
        "cpu", lambda _: FakeBackend([0.0, 0.1], calls), writer, lambda *_: True
    )
    output = tmp_path / "out.wav"
    service.synthesize(
        replace(request(tmp_path), text="ประโยคแรก. ประโยคที่สอง"),
        tmp_path / "ref.wav",
        output,
    )

    assert len(calls) == 2


def test_service_preserves_punctuation_segments_for_generation(tmp_path):
    calls = []

    def writer(path, waveform, sample_rate):
        Path(path).write_bytes(b"RIFFvalid")

    service = VoiceCloneService(
        "cpu", lambda _: FakeBackend([0.0], calls), writer, lambda *_: True
    )
    service.synthesize(
        replace(request(tmp_path), text="ประโยคแรก. ประโยคที่สอง"),
        tmp_path / "ref.wav",
        tmp_path / "out.wav",
    )

    assert [call["gen_text"] for call in calls] == ["ประโยคแรก", "ประโยคที่สอง"]
    assert all(call["ref_text"] == "ต้นฉบับ" for call in calls)


def test_service_rejects_empty_or_unreadable_output(tmp_path):
    def writer(path, waveform, sample_rate):
        Path(path).write_bytes(b"")

    service = VoiceCloneService(
        "cpu", lambda _: FakeBackend([]), writer, lambda *_: False
    )
    with pytest.raises(ModelError, match="ไฟล์เสียงผลลัพธ์"):
        service.synthesize(request(tmp_path), tmp_path / "ref.wav", tmp_path / "out.wav")


def test_service_translates_out_of_memory_and_removes_partial_output(tmp_path):
    output = tmp_path / "partial.wav"

    class OutOfMemoryBackend(FakeBackend):
        def infer(self, **kwargs):
            output.write_bytes(b"partial")
            raise RuntimeError("CUDA out of memory")

    service = VoiceCloneService(
        "cuda", lambda _: OutOfMemoryBackend(), lambda *args: None, lambda *_: True
    )
    with pytest.raises(ModelError, match="หน่วยความจำการ์ดจอ"):
        service.synthesize(request(tmp_path), tmp_path / "ref.wav", output)
    assert not output.exists()
