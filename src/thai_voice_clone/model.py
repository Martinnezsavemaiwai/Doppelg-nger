import os
from pathlib import Path
import re
from typing import Callable


class ModelError(RuntimeError):
    """Model loading or synthesis failed."""


_PAUSE_PATTERN = re.compile(r"(?P<text>.*?)(?P<marks>[,，、;；:：.!?！？。…\n]+|$)", re.DOTALL)
_THOUSANDS_COMMA = re.compile(r"(?<=\d),(?=\d)")
_DECIMAL = re.compile(r"(?<![\d.])(\d+)\.(\d+)(?![\d.])")
# ponytail: a standalone vowel-less word before "." loses its pause, a dictionary if that matters.
_ABBREVIATION = re.compile(r"(?<![฀-๿])(?:[ก-ฮ]{1,3}\.)+")


def _remove_non_clause_punctuation(text: str) -> str:
    """Rewrite numbers and abbreviations so their marks do not split clauses."""
    text = _THOUSANDS_COMMA.sub("", text)
    # f5_tts_th strips "." before reading numbers, so 3.14 would become 314.
    text = _DECIMAL.sub(lambda match: f"{match[1]} จุด {' '.join(match[2])}", text)
    return _ABBREVIATION.sub(lambda match: match[0].replace(".", "") + " ", text)


def split_generation_text(text: str) -> list[tuple[str, float]]:
    """Split generated text into clauses and return a pause after each clause."""
    segments: list[tuple[str, float]] = []
    for match in _PAUSE_PATTERN.finditer(_remove_non_clause_punctuation(text.strip())):
        segment = " ".join(match.group("text").split())
        if not segment:
            continue
        marks = match.group("marks")
        pause = 0.32 if any(mark in marks for mark in ".!?！？。…\n") else 0.16
        segments.append((segment, pause if marks else 0.0))
    return segments


def _join_waveforms(waveforms: list[tuple[object, float]], sample_rate: int):
    if len(waveforms) == 1 and waveforms[0][1] == 0:
        return waveforms[0][0]

    import numpy as np

    parts = []
    for waveform, pause in waveforms:
        audio = np.asarray(waveform, dtype=np.float32).reshape(-1)
        if audio.size:
            parts.append(audio)
        if pause and audio.size:
            parts.append(np.zeros(round(pause * sample_rate), dtype=np.float32))
    if not parts:
        return np.asarray([], dtype=np.float32)
    return np.concatenate(parts)


def select_device(
    mode: str,
    cuda_available: Callable[[], bool],
    cuda_probe: Callable[[], None],
) -> str:
    if mode == "cpu":
        return "cpu"
    if not cuda_available():
        if mode == "cuda":
            raise ModelError("ไม่พบ CUDA ที่ใช้งานได้")
        return "cpu"
    try:
        cuda_probe()
    except Exception as exc:
        if mode == "cuda":
            raise ModelError("CUDA เริ่มทำงานไม่สำเร็จ") from exc
        return "cpu"
    return "cuda"


class VoiceCloneService:
    def __init__(
        self,
        device: str,
        backend_factory: Callable,
        wav_writer: Callable,
        wav_verifier: Callable[[Path], bool],
    ) -> None:
        self.device = device
        self.backend_factory = backend_factory
        self.wav_writer = wav_writer
        self.wav_verifier = wav_verifier
        self._cache: dict[tuple[str, str], object] = {}

    def synthesize(self, request, normalized_reference, output_path) -> Path:
        output_path = Path(output_path)
        try:
            key = (request.model, self.device)
            if key not in self._cache:
                self._cache[key] = self.backend_factory(request.model, self.device)
            segments = split_generation_text(request.text)
            waveform = _join_waveforms(
                [
                    (
                        self._cache[key].infer(
                            ref_audio=str(normalized_reference),
                            ref_text=request.reference_text,
                            gen_text=segment,
                            step=32,
                            speed=request.speed,
                            cfg=2.0,
                            max_chars=100,
                        ),
                        pause,
                    )
                    for segment, pause in segments
                ],
                24000,
            )
            self.wav_writer(output_path, waveform, 24000)
            if (
                not output_path.is_file()
                or output_path.stat().st_size == 0
                or not self.wav_verifier(output_path)
            ):
                raise ModelError("ไฟล์เสียงผลลัพธ์ไม่สมบูรณ์")
            return output_path
        except ModelError:
            output_path.unlink(missing_ok=True)
            raise
        except Exception as exc:
            output_path.unlink(missing_ok=True)
            if "out of memory" in str(exc).lower():
                self._cache.clear()
                _clear_cuda_cache()
                raise ModelError(
                    "หน่วยความจำการ์ดจอไม่พอ กรุณาปิดโปรแกรมที่ใช้ GPU "
                    "หรือลองโหมด CPU"
                ) from exc
            raise ModelError(
                "สังเคราะห์เสียงไม่สำเร็จ โปรดดูรายละเอียดในหน้าต่างคำสั่ง"
            ) from exc


def _clear_cuda_cache() -> None:
    try:
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass


def create_f5_backend(model: str, device: str):
    if device == "cpu":
        import torch

        # f5_tts_th has no device option; it asks torch once when imported.
        torch.cuda.is_available = lambda: False

    from f5_tts_th.tts import TTS

    return TTS(model=model)


def write_wav(path: Path, waveform, sample_rate: int) -> None:
    import soundfile

    soundfile.write(path, waveform, sample_rate)


def verify_wav(path: Path) -> bool:
    import soundfile

    try:
        info = soundfile.info(path)
    except Exception:
        return False
    return info.frames > 0 and info.samplerate == 24000


def create_service(settings) -> VoiceCloneService:
    if settings.device_mode == "cpu":
        os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

    import torch

    def probe() -> None:
        torch.empty(1, device="cuda")

    device = select_device(settings.device_mode, torch.cuda.is_available, probe)
    return VoiceCloneService(device, create_f5_backend, write_wav, verify_wav)
