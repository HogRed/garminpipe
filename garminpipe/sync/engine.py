from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import pandas as pd

from garminpipe.clients.garth_client import GarthClient
from garminpipe.store.parquet_store import ParquetStore


def _safe_get(d: Dict[str, Any], path: List[str], default=None):
    cur: Any = d
    for k in path:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


@dataclass
class SyncEngine:
    client: GarthClient
    store: ParquetStore
    lookback_days: int = 2
    page_limit: int = 100

    def sync(self, until: Optional[date] = None) -> pd.DataFrame:
        """
        Incremental sync based on cursor.json. Uses a lookback window to capture edits/late uploads.
        Writes to Parquet and returns the newly ingested canonical rows.
        """
        until = until or datetime.now(timezone.utc).date()

        cursor = self.store.get_cursor()
        last_end = cursor.get("last_end_date")  # ISO date string
        if last_end:
            start_date = date.fromisoformat(last_end) - timedelta(days=self.lookback_days)
        else:
            # first run: default to 30 days
            start_date = until - timedelta(days=30)

        all_rows: List[Dict[str, Any]] = []
        start = 0

        while True:
            batch = self.client.list_activities(
                start_date=start_date,
                end_date=until,
                start=start,
                limit=self.page_limit,
            )
            if not batch:
                break

            all_rows.extend(batch)

            # Pagination: if returned less than limit, we're done
            if len(batch) < self.page_limit:
                break

            start += self.page_limit

        df_new = self._map_to_canonical(all_rows)
        self.store.upsert_activities(df_new)

        # update cursor
        cursor_out = {
            "last_end_date": until.isoformat(),
            "updated_at_utc": self.store.now_utc_iso(),
            "lookback_days": self.lookback_days,
        }
        self.store.set_cursor(cursor_out)

        return df_new

    def _map_to_canonical(self, activities: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Map Garmin activity summaries -> canonical activity table.
        Fields vary; mapping is defensive and will evolve.
        """
        ingested_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

        rows = []
        for a in activities:
            activity_id = a.get("activityId")
            if activity_id is None:
                continue

            # Prefer GMT timestamp if present; keep local too
            start_time_gmt = a.get("startTimeGMT") or a.get("startTimeGmt")
            start_time_local = a.get("startTimeLocal")

            rows.append(
                {
                    "activity_id": str(activity_id),
                    "name": a.get("activityName") or a.get("activityName") or a.get("name"),
                    "activity_type": _safe_get(a, ["activityType", "typeKey"], default=None),
                    "start_time_gmt": start_time_gmt,
                    "start_time_local": start_time_local,
                    "duration_s": a.get("duration"),
                    "moving_duration_s": a.get("movingDuration"),
                    "elapsed_duration_s": a.get("elapsedDuration"),
                    "distance_m": a.get("distance"),
                    "avg_hr_bpm": a.get("averageHR"),
                    "max_hr_bpm": a.get("maxHR"),
                    "calories_kcal": a.get("calories"),
                    "elevation_gain_m": a.get("elevationGain"),
                    "device_name": a.get("deviceName"),
                    "ingested_at": ingested_at,
                    "source": "garth",
                }
            )

        df = pd.DataFrame(rows)
        if df.empty:
            return df

        # Normalize types
        numeric_cols = [
            "duration_s",
            "moving_duration_s",
            "elapsed_duration_s",
            "distance_m",
            "avg_hr_bpm",
            "max_hr_bpm",
            "calories_kcal",
            "elevation_gain_m",
        ]
        for c in numeric_cols:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")

        # Parse datetimes (keep as string if parsing fails)
        if "start_time_gmt" in df.columns:
            df["start_time"] = pd.to_datetime(df["start_time_gmt"], errors="coerce", utc=True)
        else:
            df["start_time"] = pd.NaT

        return df
