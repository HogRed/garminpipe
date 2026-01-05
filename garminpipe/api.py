from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd

from garminpipe.config import GarminPipeConfig
from garminpipe.clients.garth_client import GarthClient
from garminpipe.store.parquet_store import ParquetStore
from garminpipe.sync.engine import SyncEngine
from garminpipe.transform.clean import clean_activities
from garminpipe.transform.aggregates import weekly_rollup


@dataclass
class GarminPipe:
    config: GarminPipeConfig = GarminPipeConfig()
    last_sync_summary: dict | None = None

    def __post_init__(self) -> None:
        self.config.ensure_dirs()
        self._client = GarthClient(session_dir=self.config.session_dir)
        self._store = ParquetStore(data_dir=self.config.data_dir)
        self._sync = SyncEngine(
            client=self._client,
            store=self._store,
            lookback_days=self.config.lookback_days,
            page_limit=self.config.page_limit,
        )

    def login(self, email: str, password: str, prompt_mfa=None) -> None:
        self._client.resume_or_login(email=email, password=password, prompt_mfa=prompt_mfa)

    def sync(self) -> pd.DataFrame:
        df_new = self._sync.sync()
        self.last_sync_summary = getattr(self._sync, "last_summary", None)
        return df_new

    def activities(self) -> pd.DataFrame:
        return self._store.read_activities()

    def clean(self, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        return clean_activities(df if df is not None else self.activities())

    def weekly(self, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        cleaned = self.clean(df)
        return weekly_rollup(cleaned)

    def resume(self) -> bool:
        return self._client.resume()