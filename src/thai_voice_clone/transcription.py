from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Callable


class TranscriptionError(RuntimeError):
    """A local transcription request could not be completed."""


@dataclass(frozen=True)
class TranscriptionResult:
    text: str
    duration: float
    language: str | None


WORKER_RESULT_PREFIX = "DOPPELGANGER_TRANSCRIPTION_RESULT:"
_WORKER_MODULE = "thai_voice_clone.transcription_worker"
_WORKER_ERROR = "ถอดข้อความจากเสียงไม่สำเร็จ คุณยังสามารถกรอกข้อความเองได้"


def _default_model_factory(model_name: str, device: str, compute_type: str):
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise TranscriptionError(
            "ยังไม่ได้ติดตั้ง faster-whisper โปรดรัน .\\setup.ps1 แล้วลองใหม่"
        ) from exc
    return WhisperModel(
        model_name,
        device=device,
        compute_type=compute_type,
    )


class LocalWhisperTranscriber:
    def __init__(
        self,
        settings,
        model_factory: Callable = _default_model_factory,
    ) -> None:
        self.settings = settings
        self.model_factory = model_factory
        self._models: dict[tuple[str, str, str], object] = {}

    def _model_config(self) -> tuple[str, str, str]:
        model_name = os.getenv("THAI_VOICE_WHISPER_MODEL", "small").strip() or "small"
        configured_device = os.getenv("THAI_VOICE_WHISPER_DEVICE", "cpu").strip().lower()
        if configured_device not in {"cpu", "cuda", "auto"}:
            raise TranscriptionError(
                "THAI_VOICE_WHISPER_DEVICE ต้องเป็น cpu, cuda หรือ auto"
            )
        device = configured_device
        if configured_device == "auto":
            device = "cuda" if self.settings.device_mode == "cuda" else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"
        return model_name, device, compute_type

    def _get_model(self):
        config = self._model_config()
        if config not in self._models:
            try:
                self._models[config] = self.model_factory(*config)
            except TranscriptionError:
                raise
            except ImportError as exc:
                raise TranscriptionError(
                    "ยังไม่ได้ติดตั้ง faster-whisper โปรดรัน .\\setup.ps1 แล้วลองใหม่"
                ) from exc
            except Exception as exc:
                raise TranscriptionError(
                    "โหลดโมเดลถอดเสียงไม่สำเร็จ โปรดลองใหม่หรือใช้การกรอกข้อความเอง"
                ) from exc
        return self._models[config]

    def transcribe(self, path: str | Path) -> TranscriptionResult:
        source = Path(path)
        if not source.is_file():
            raise TranscriptionError("ไม่พบไฟล์เสียงสำหรับถอดข้อความ")
        try:
            segments, info = self._get_model().transcribe(
                str(source),
                language="th",
                vad_filter=True,
                beam_size=5,
            )
            text = " ".join(
                segment.text.strip() for segment in segments if segment.text.strip()
            ).strip()
        except TranscriptionError:
            raise
        except Exception as exc:
            raise TranscriptionError(
                "ถอดข้อความจากเสียงไม่สำเร็จ คุณยังสามารถกรอกข้อความเองได้"
            ) from exc
        if not text:
            raise TranscriptionError(
                "ไม่พบคำพูดที่ชัดเจนในไฟล์เสียง คุณสามารถกรอกข้อความเองได้"
            )
        return TranscriptionResult(
            text=text,
            duration=float(getattr(info, "duration", 0.0) or 0.0),
            language=getattr(info, "language", None),
        )


class SubprocessWhisperTranscriber:
    """Run Whisper outside the API process to isolate native runtimes."""

    def __init__(self, settings, runner: Callable = subprocess.run) -> None:
        self.settings = settings
        self.runner = runner

    def transcribe(self, path: str | Path) -> TranscriptionResult:
        source = Path(path)
        if not source.is_file():
            raise TranscriptionError("ไม่พบไฟล์เสียงสำหรับถอดข้อความ")

        command = [sys.executable, "-m", _WORKER_MODULE, str(source)]
        try:
            completed = self.runner(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=os.environ.copy(),
                timeout=900,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise TranscriptionError(_WORKER_ERROR) from exc

        payload = _read_worker_payload(completed.stdout)
        if completed.returncode != 0:
            detail = payload.get("error") if isinstance(payload, dict) else None
            raise TranscriptionError(detail or _WORKER_ERROR)
        if not isinstance(payload, dict):
            raise TranscriptionError(_WORKER_ERROR)

        text = payload.get("text")
        duration = payload.get("duration")
        language = payload.get("language")
        if not isinstance(text, str) or not text.strip():
            raise TranscriptionError(_WORKER_ERROR)
        try:
            duration = float(duration)
        except (TypeError, ValueError) as exc:
            raise TranscriptionError(_WORKER_ERROR) from exc
        if language is not None and not isinstance(language, str):
            raise TranscriptionError(_WORKER_ERROR)
        return TranscriptionResult(text=text, duration=duration, language=language)


def _read_worker_payload(stdout: str) -> dict | None:
    for line in reversed(stdout.splitlines()):
        if not line.startswith(WORKER_RESULT_PREFIX):
            continue
        try:
            payload = json.loads(line[len(WORKER_RESULT_PREFIX) :])
        except json.JSONDecodeError:
            return None
        return payload if isinstance(payload, dict) else None
    return None
