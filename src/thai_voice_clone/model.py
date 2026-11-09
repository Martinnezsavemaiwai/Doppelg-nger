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
    # Read decimals digit by digit in Thai; "." would otherwise split the clause.
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
        self._backend = None

    def synthesize(self, request, normalized_reference, output_path) -> Path:
        output_path = Path(output_path)
        try:
            if self._backend is None:
                self._backend = self.backend_factory(self.device)
            backend = self._backend
            sample_rate = backend.sample_rate
            segments = split_generation_text(request.text)
            waveform = _join_waveforms(
                [
                    (
                        backend.infer(
                            ref_audio=str(normalized_reference),
                            ref_text=request.reference_text,
                            gen_text=segment,
                        ),
                        pause,
                    )
                    for segment, pause in segments
                ],
                sample_rate,
            )
            self.wav_writer(output_path, waveform, sample_rate)
            if (
                not output_path.is_file()
                or output_path.stat().st_size == 0
                or not self.wav_verifier(output_path, sample_rate)
            ):
                raise ModelError("ไฟล์เสียงผลลัพธ์ไม่สมบูรณ์")
            return output_path
        except ModelError:
            output_path.unlink(missing_ok=True)
            raise
        except Exception as exc:
            output_path.unlink(missing_ok=True)
            if "out of memory" in str(exc).lower():
                self._backend = None
                _clear_cuda_cache()
                raise ModelError(
                    "หน่วยความจำการ์ดจอไม่พอ ปิดโปรแกรมที่ใช้ GPU แล้วลองอีกครั้ง"
                ) from exc
            raise ModelError(
                "สร้างเสียงไม่สำเร็จ ดูรายละเอียดใน outputs/logs/backend.error.log"
            ) from exc


def _clear_cuda_cache() -> None:
    try:
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass


VOXCPM_MODEL_ID = "openbmb/VoxCPM2"


class VoxCPMBackend:
    def __init__(self, device: str) -> None:
        import torch
        from voxcpm import VoxCPM

        # VoxCPM builds the 2B model in float32 before casting to bfloat16, which
        # commits ~16 GB and can crash a 16 GB machine before the pagefile grows.
        # Building in bfloat16 peaks at ~13 GB; RoPE buffers pin float32 explicitly
        # and every weight is overwritten from the checkpoint, so output is the same.
        previous_dtype = torch.get_default_dtype()
        torch.set_default_dtype(torch.bfloat16)
        try:
            self._model = VoxCPM.from_pretrained(
                VOXCPM_MODEL_ID, load_denoiser=False, device=device
            )
        finally:
            torch.set_default_dtype(previous_dtype)
        self.sample_rate = self._model.tts_model.sample_rate

    def infer(self, ref_audio: str, ref_text: str, gen_text: str):
        # Same clip as prompt and reference gives the closest voice match (VoxCPM docs).
        return self._model.generate(
            text=gen_text,
            prompt_wav_path=ref_audio,
            prompt_text=ref_text,
            reference_wav_path=ref_audio,
            cfg_value=2.0,
            inference_timesteps=10,
        )


def write_wav(path: Path, waveform, sample_rate: int) -> None:
    import soundfile

    soundfile.write(path, waveform, sample_rate)


def verify_wav(path: Path, sample_rate: int) -> bool:
    import soundfile

    try:
        info = soundfile.info(path)
    except Exception:
        return False
    return info.frames > 0 and info.samplerate == sample_rate


def create_service(settings) -> VoiceCloneService:
    if settings.device_mode == "cpu":
        os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

    import torch

    def probe() -> None:
        torch.empty(1, device="cuda")

    device = select_device(settings.device_mode, torch.cuda.is_available, probe)
    return VoiceCloneService(device, VoxCPMBackend, write_wav, verify_wav)
