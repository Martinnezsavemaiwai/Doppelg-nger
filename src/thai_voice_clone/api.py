from __future__ import annotations

from contextlib import contextmanager
import os
import shutil
import tempfile
from pathlib import Path
from typing import Callable

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .app import generate
from .audio import AudioPreparationError
from .config import DEFAULT_SYNTHESIS_SPEED, load_settings
from .model import ModelError, create_service
from .transcription import SubprocessWhisperTranscriber, TranscriptionError
from .validation import UserInputError


ALLOWED_SUFFIXES = {".wav", ".mp3", ".m4a", ".flac", ".webm"}
MODEL_OPTIONS = [
    {"id": "v1", "label": "V1 อ่านภาษาไทยทั่วไป"},
    {"id": "v2", "label": "V2 ลดการอ่านข้ามและอ่านซ้ำ"},
]


def _split_status(status: str) -> tuple[str, str | None]:
    message, separator, warning = status.partition(" — ")
    return message, warning if separator else None


def _allowed_origins() -> list[str]:
    configured = os.getenv(
        "THAI_VOICE_FRONTEND_ORIGINS",
        "http://127.0.0.1:5173,http://localhost:5173",
    )
    return [origin.strip() for origin in configured.split(",") if origin.strip()]


@contextmanager
def _saved_upload(reference: UploadFile):
    suffix = Path(reference.filename or "").suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(
            status_code=400,
            detail="รองรับเฉพาะไฟล์ WAV, MP3, M4A, FLAC หรือ WebM",
        )
    with tempfile.TemporaryDirectory(prefix="doppelganger-upload-") as temp_dir:
        reference_path = Path(temp_dir) / f"reference{suffix}"
        with reference_path.open("wb") as destination:
            shutil.copyfileobj(reference.file, destination)
        yield reference_path


def create_api(
    settings=None,
    service_factory: Callable = create_service,
    generate_fn: Callable = generate,
    transcribe_fn: Callable | None = None,
    transcriber_factory: Callable | None = None,
) -> FastAPI:
    settings = settings or load_settings()
    transcriber_factory = transcriber_factory or SubprocessWhisperTranscriber
    cached_service = None
    cached_transcriber = None

    def get_service():
        nonlocal cached_service
        if cached_service is None:
            cached_service = service_factory(settings)
        return cached_service

    def transcribe_file(path: Path):
        nonlocal cached_transcriber
        if transcribe_fn is not None:
            return transcribe_fn(path, settings)
        if cached_transcriber is None:
            cached_transcriber = transcriber_factory(settings)
        return cached_transcriber.transcribe(path)

    app = FastAPI(
        title="ด็อปเปิลเก็งเงอร์ API",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url=None,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_allowed_origins(),
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "doppelganger"}

    @app.get("/api/models")
    def models() -> dict[str, list[dict[str, str]]]:
        return {"models": MODEL_OPTIONS}

    @app.post("/api/synthesize")
    def synthesize(
        reference: UploadFile = File(...),
        reference_text: str = Form(...),
        text: str = Form(...),
        model: str = Form("v1"),
        speed: float = Form(DEFAULT_SYNTHESIS_SPEED),
    ) -> dict[str, str | None]:
        with _saved_upload(reference) as reference_path:
            try:
                status, _, output = generate_fn(
                    reference_path,
                    reference_text,
                    text,
                    model,
                    speed,
                    service=get_service(),
                    output_factory=settings.new_output_path,
                )
            except UserInputError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            except AudioPreparationError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            except ModelError as exc:
                raise HTTPException(status_code=500, detail=str(exc)) from exc

        message, warning = _split_status(status)
        output_path = Path(output)
        try:
            relative_name = output_path.resolve().relative_to(settings.output_dir.resolve())
        except ValueError as exc:
            raise HTTPException(status_code=500, detail="ไฟล์ผลลัพธ์อยู่นอกโฟลเดอร์ที่อนุญาต") from exc
        return {
            "status": message,
            "warning": warning,
            "audio_url": f"/api/outputs/{relative_name.as_posix()}",
        }

    @app.post("/api/transcribe")
    def transcribe(reference: UploadFile = File(...)) -> dict[str, str | float | None]:
        with _saved_upload(reference) as reference_path:
            try:
                result = transcribe_file(reference_path)
            except TranscriptionError as exc:
                raise HTTPException(status_code=503, detail=str(exc)) from exc
        return {
            "text": result.text,
            "duration": result.duration,
            "language": result.language,
        }

    @app.get("/api/outputs/{filename}")
    def output(filename: str) -> FileResponse:
        candidate_name = Path(filename)
        if candidate_name.name != filename or candidate_name.suffix.lower() != ".wav":
            raise HTTPException(status_code=404, detail="ไม่พบไฟล์เสียง")
        output_dir = settings.output_dir.resolve()
        candidate = (output_dir / candidate_name).resolve()
        try:
            candidate.relative_to(output_dir)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail="ไม่พบไฟล์เสียง") from exc
        if not candidate.is_file():
            raise HTTPException(status_code=404, detail="ไม่พบไฟล์เสียง")
        return FileResponse(candidate, media_type="audio/wav", filename=candidate.name)

    return app


app = create_api()
