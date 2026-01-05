from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd


@dataclass
class ParquetStore:
    data_dir: Path

    @property
    def activities_path(self) -> Path:
        return self.data_dir / "activities.parquet"

    @property
    def cursor_path(self) -> Path:
        return self.data_dir / "cursor.json"

    def read_activities(self) -> pd.DataFrame:
        if not self.activities_path.exists():
            return pd.DataFrame()
        return pd.read_parquet(self.activities_path)

    def upsert_activities(self, df_new: pd.DataFrame) -> None:
        if df_new.empty:
            return

        df_old = self.read_activities()
        if df_old.empty:
            df = df_new
        else:
            df = pd.concat([df_old, df_new], ignore_index=True)

        # Deduplicate by primary key, keep last ingested row
        if "ingested_at" in df.columns:
            df = df.sort_values("ingested_at")
        df = df.drop_duplicates(subset=["activity_id"], keep="last")

        df.to_parquet(self.activities_path, index=False)

    def get_cursor(self) -> Dict[str, Any]:
        if not self.cursor_path.exists():
            return {}
        return json.loads(self.cursor_path.read_text(encoding="utf-8"))

    def set_cursor(self, cursor: Dict[str, Any]) -> None:
        self.cursor_path.write_text(json.dumps(cursor, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def now_utc_iso() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
