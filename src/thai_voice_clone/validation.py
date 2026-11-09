from dataclasses import dataclass
from pathlib import Path
import re


class UserInputError(ValueError):
    """An error that can be shown directly to the user."""


@dataclass(frozen=True)
class GenerationRequest:
    reference: Path
    reference_text: str
    text: str
    model: str
    speed: float
    warning: str | None = None


def _clean(value: str) -> str:
    return " ".join((value or "").split())


def _clean_lines(value: str) -> str:
    lines = (_clean(line) for line in (value or "").splitlines())
    return "\n".join(line for line in lines if line)


def validate_request(
    reference: str | Path | None,
    reference_text: str,
    text: str,
    model: str,
    speed: float,
    duration: float,
) -> GenerationRequest:
    path = Path(reference) if reference else None
    if not path or not path.is_file():
        raise UserInputError("กรุณาเลือกไฟล์เสียงต้นฉบับ")
    if path.suffix.lower() not in {".wav", ".mp3", ".m4a", ".flac", ".webm"}:
        raise UserInputError("รองรับเฉพาะไฟล์ WAV, MP3, M4A, FLAC หรือ WebM")

    normalized_reference_text = _clean(reference_text)
    normalized_text = _clean_lines(text)
    if not normalized_reference_text:
        raise UserInputError("กรุณากรอกข้อความต้นฉบับให้ตรงกับเสียง")
    if not any(character.isalnum() for character in normalized_text):
        raise UserInputError("กรุณากรอกข้อความที่ต้องการสังเคราะห์")
    if len(normalized_text) > 500:
        raise UserInputError("ข้อความต้องไม่เกิน 500 ตัวอักษร")
    if model not in {"v1", "v2"}:
        raise UserInputError("โมเดลต้องเป็น v1 หรือ v2")
    if not 0.7 <= float(speed) <= 1.2:
        raise UserInputError("ความเร็วต้องอยู่ระหว่าง 0.7 ถึง 1.2")
    if not 2.0 <= float(duration) <= 15.0:
        raise UserInputError("เสียงต้นฉบับต้องยาว 2 ถึง 15 วินาที")

    warnings = []
    if not 4.0 <= float(duration) <= 8.0:
        warnings.append("แนะนำเสียงต้นฉบับยาว 4 ถึง 8 วินาที")
    if re.search(r"[A-Za-z]", normalized_reference_text):
        warnings.append("คำอังกฤษในข้อความต้นฉบับควรเขียนเป็นคำอ่านไทยเพื่อให้เสียงคล้ายขึ้น")
    return GenerationRequest(
        reference=path,
        reference_text=normalized_reference_text,
        text=normalized_text,
        model=model,
        speed=float(speed),
        warning="; ".join(warnings) or None,
    )
