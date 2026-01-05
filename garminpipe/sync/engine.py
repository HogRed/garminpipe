from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import pandas as pd

from garminpipe.clients.garth_client import GarthClient
from garminpipe.store.parquet_store import ParquetStore

# helper to safely get nested dict values
def _safe_get(d: Dict[str, Any], path: List[str], default=None):
    # traverse dict along path
    cur: Any = d
    for k in path:
        # if current is not a dict or key not present, return default
        if not isinstance(cur, dict) or k not in cur:
            return default
        # advance to next level
        cur = cur[k]
    return cur

# sync engine dataclass for incremental sync
@dataclass
class SyncEngine:
    # class attributes
    client: GarthClient
    store: ParquetStore
    lookback_days: int = 2
    page_limit: int = 100

    last_summary: Dict[str, Any] | None = None

    # method to perform sync
    def sync(self, until: Optional[date] = None) -> pd.DataFrame:
        # determine end date
        until = until or datetime.now(timezone.utc).date()

        # load existing cursor
        cursor = self.store.get_cursor()
        # determine start date with lookback
        last_end = cursor.get("last_end_date")

        # if last end date exists, use it minus lookback
        if last_end:
            start_date = date.fromisoformat(last_end) - timedelta(days=self.lookback_days)

        # else default to 30 days ago
        else:
            start_date = until - timedelta(days=30)

        # fetch all activities in pages
        all_rows: List[Dict[str, Any]] = []
        start = 0

        # pagination loop
        while True:
            # fetch a page of activities
            batch = self.client.list_activities(
                start_date=start_date,
                end_date=until,
                start=start,
                limit=self.page_limit,
            )
            # break if no more activities
            if not batch:
                break

            # accumulate fetched activities
            all_rows.extend(batch)

            # break if the page is smaller than limit, because that means we're done
            if len(batch) < self.page_limit:
                break

            # advance start for next page
            start += self.page_limit

        # total number of activities
        fetched = len(all_rows)

        # map to canonical dataframe
        df_new = self._map_to_canonical(all_rows)

        # ensure row_hash exists for change detection
        if not df_new.empty:
            df_new = df_new.copy() # copy
            df_new["row_hash"] = self.store.compute_row_hash(df_new)

        # upsert into store and get summary
        summary = self.store.upsert_activities(df_new)

        # store last summary for API/CLI
        self.last_summary = {
            **summary, # unpack dictionary
            "fetched": fetched,
            "start_date": start_date.isoformat(),
            "end_date": until.isoformat(),
        }
        
        # update cursor with new end date and fetched count
        cursor_out = {
            "last_start_date": start_date.isoformat(),
            "last_end_date": until.isoformat(),
            "updated_at_utc": self.store.now_utc_iso(),
            "lookback_days": self.lookback_days,
            "last_fetched": fetched,
        }
        # set updated cursor
        self.store.set_cursor(cursor_out)

        # updated df
        return df_new

    def _map_to_canonical(self, activities: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Map Garmin activity summaries -> canonical activity table.
        Fields vary; mapping is defensive and will evolve.
        """
        # current ingestion timestamp
        ingested_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

        # map each activity to canonical row
        rows = []
        for a in activities:
            activity_id = a.get("activityId")
            if activity_id is None:
                continue # skip

            # prefer GMT timestamp if present; keep local too
            start_time_gmt = a.get("startTimeGMT") or a.get("startTimeGmt")
            start_time_local = a.get("startTimeLocal")

            # append mapped row
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

        # create dataframe
        df = pd.DataFrame(rows)
        if df.empty:
            return df

        # normalize types
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

        # parse datetimes (keep as string if parsing fails)
        if "start_time_gmt" in df.columns:
            df["start_time"] = pd.to_datetime(df["start_time_gmt"], errors="coerce", utc=True)
        else:
            df["start_time"] = pd.NaT # not a time

        return df