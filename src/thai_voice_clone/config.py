from dataclasses import dataclass
from datetime import datetime
import os
from pathlib import Path
import secrets


DEFAULT_SYNTHESIS_SPEED = 0.8


@dataclass(frozen=True)
class Settings:
    root: Path
    device_mode: str

    @property
    def output_dir(self) -> Path:
        return self.root / "outputs" / "generated"

    @property
    def default_reference(self) -> Path:
        return self.root / "data" / "reference" / "user_voice.wav"

    def new_output_path(
        self,
        now: datetime | None = None,
        token: str | None = None,
    ) -> Path:
        stamp = (now or datetime.now()).strftime("%Y%m%d-%H%M%S")
        suffix = token or secrets.token_hex(3)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        return self.output_dir / f"voice-{stamp}-{suffix}.wav"


def load_settings(root: str | Path | None = None) -> Settings:
    resolved_root = Path(root or Path(__file__).resolve().parents[2])
    mode = os.getenv("THAI_VOICE_DEVICE", "auto").strip().lower()
    if mode not in {"auto", "cuda", "cpu"}:
        raise ValueError("THAI_VOICE_DEVICE ต้องเป็น auto, cuda หรือ cpu")
    return Settings(root=resolved_root, device_mode=mode)
