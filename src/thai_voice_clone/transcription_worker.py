from __future__ import annotations

import json
import sys
from pathlib import Path

from .config import load_settings
from .transcription import (
    WORKER_RESULT_PREFIX,
    LocalWhisperTranscriber,
    TranscriptionError,
)


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 1:
        _write_result({"error": "ไม่พบไฟล์เสียงสำหรับถอดข้อความ"})
        return 2

    try:
        result = LocalWhisperTranscriber(load_settings()).transcribe(Path(args[0]))
    except TranscriptionError as exc:
        _write_result({"error": str(exc)})
        return 1
    except Exception:
        _write_result(
            {"error": "ถอดข้อความจากเสียงไม่สำเร็จ คุณยังสามารถกรอกข้อความเองได้"}
        )
        return 1

    _write_result(
        {
            "text": result.text,
            "duration": result.duration,
            "language": result.language,
        }
    )
    return 0


def _write_result(payload: dict) -> None:
    print(
        WORKER_RESULT_PREFIX + json.dumps(payload, ensure_ascii=False),
        flush=True,
    )


if __name__ == "__main__":
    # The parent decodes UTF-8; a piped stdout on Windows defaults to the ANSI code page.
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
