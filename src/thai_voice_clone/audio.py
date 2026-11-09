from contextlib import contextmanager
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Callable, Iterator


class AudioPreparationError(RuntimeError):
    """Audio could not be inspected or normalized."""


def _run_tool(runner: Callable, args: list[str]):
    try:
        return runner(args, capture_output=True, text=True, shell=False)
    except OSError as exc:
        raise AudioPreparationError(
            "เรียกใช้ FFmpeg ไม่ได้ กรุณาติดตั้ง FFmpeg แล้วเปิดโปรแกรมใหม่"
        ) from exc


def probe_duration(
    path: str | Path,
    runner: Callable = subprocess.run,
) -> float:
    result = _run_tool(
        runner,
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(Path(path)),
        ],
    )
    try:
        duration = float(result.stdout.strip())
    except (TypeError, ValueError):
        duration = 0.0
    if result.returncode != 0 or duration <= 0:
        raise AudioPreparationError("อ่านไฟล์เสียงไม่ได้ กรุณาตรวจไฟล์หรือ FFmpeg")
    return duration


@contextmanager
def prepared_reference(
    path: str | Path,
    runner: Callable = subprocess.run,
) -> Iterator[Path]:
    temp_dir = Path(tempfile.mkdtemp(prefix="thai-voice-"))
    output = temp_dir / "reference.wav"
    try:
        result = _run_tool(
            runner,
            [
                "ffmpeg",
                "-nostdin",
                "-y",
                "-i",
                str(Path(path)),
                "-vn",
                "-ac",
                "1",
                "-ar",
                "24000",
                "-c:a",
                "pcm_s16le",
                str(output),
            ],
        )
        if result.returncode != 0 or not output.is_file() or output.stat().st_size == 0:
            raise AudioPreparationError(
                "แปลงไฟล์เสียงไม่สำเร็จ กรุณาตรวจไฟล์หรือ FFmpeg"
            )
        yield output
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
