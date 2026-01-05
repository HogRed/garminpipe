from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

APP_NAME = "garminpipe"

@dataclass(frozen=True)
class GarminPipeConfig:
    # Where Parquet + cursor.json live
    data_dir: Path = Path.home() / f"{APP_NAME}-data"

    # Where garth saves its session (tokens/cookies)
    session_dir: Path = Path.home() / ".config" / APP_NAME / "garth"

    # Sync behavior
    lookback_days: int = 2           # safety window for edited/late-uploaded activities
    page_limit: int = 100            # pagination page size for activity list calls

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.session_dir.mkdir(parents=True, exist_ok=True)
