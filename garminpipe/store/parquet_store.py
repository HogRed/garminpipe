from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import pandas as pd

# ParquetStore for GarminPipe with upsert and change detection
@dataclass
class ParquetStore:
    data_dir: Path
    # define paths for activities and cursor files
    @property
    def activities_path(self) -> Path:
        return self.data_dir / "activities.parquet"

    @property
    def cursor_path(self) -> Path:
        return self.data_dir / "cursor.json"

    # method to read activities from parquet
    def read_activities(self) -> pd.DataFrame:
        if not self.activities_path.exists():
            return pd.DataFrame()
        return pd.read_parquet(self.activities_path)

    # method to compute row hash for change detection
    @staticmethod
    def compute_row_hash(df: pd.DataFrame) -> pd.Series:
        """
        Stable-ish fingerprint for change detection.
        Round numeric fields to avoid tiny float jitter causing false updates.
        """
        # cols of note
        cols = [
            "name",
            "activity_type",
            "start_time_gmt",
            "duration_s",
            "distance_m",
            "avg_hr_bpm",
            "max_hr_bpm",
            "calories_kcal",
            "elevation_gain_m",
            "device_name",
        ]

        # temp df
        tmp = pd.DataFrame()

        # populate cols
        for c in cols:
            tmp[c] = df[c] if c in df.columns else ""

        # normalize numeric columns
        numeric_cols = ["duration_s", "distance_m", "avg_hr_bpm", "max_hr_bpm", 
                        "calories_kcal", "elevation_gain_m"]
        
        for c in numeric_cols:
            tmp[c] = pd.to_numeric(tmp[c], errors="coerce").round(3)

        # strings, NaNs -> ""
        tmp = tmp.fillna("").astype(str)

        # compute sha256 hash of concatenated row values
        row_str = tmp.agg("|".join, axis=1)
        return row_str.map(lambda s: hashlib.sha256(s.encode("utf-8")).hexdigest())


    def upsert_activities(self, df_new: pd.DataFrame) -> Dict[str, int]:
        """
        Upsert by activity_id with change detection using row_hash.
        Returns counts for inserted/updated/unchanged + total after write.
        """
        # early return if no new data
        if df_new.empty:
            df_old = self.read_activities()
            return {"inserted": 0, "updated": 0, "unchanged": 0, "total": int(len(df_old))}

        # if caller didn't compute row_hash, compute it here
        if "row_hash" not in df_new.columns:
            df_new = df_new.copy()
            df_new["row_hash"] = self.compute_row_hash(df_new)

        # deduplicate incoming by activity_id (keep last ingested)
        if "ingested_at" in df_new.columns:
            df_new = df_new.sort_values("ingested_at")

        # drop duplicates
        df_new = df_new.drop_duplicates(subset=["activity_id"], keep="last")

        # read existing activities
        df_old = self.read_activities()

        # if empty, just write new and return
        if df_old.empty:
            df_new.to_parquet(self.activities_path, index=False)
            return {"inserted": int(len(df_new)), "updated": 0, "unchanged": 0, "total": int(len(df_new))}

        # ensure old has row_hash (older parquet may not)
        df_old = df_old.copy() # copy of df

        if "row_hash" not in df_old.columns:
            df_old["row_hash"] = self.compute_row_hash(df_old)

        # index by activity_id for comparison/upsert
        old_idx = df_old.set_index("activity_id", drop=False)
        new_idx = df_new.set_index("activity_id", drop=False)

        # get sets of IDs
        old_ids = set(old_idx.index.astype(str))
        new_ids = set(new_idx.index.astype(str))

        # get new and shared IDs
        inserted_ids = new_ids - old_ids
        common_ids = new_ids & old_ids

        # updated vs unchanged based on row_hash
        updated_ids = set()
        unchanged_ids = set()
        for aid in common_ids:
            # compare row_hash
            old_h = old_idx.at[aid, "row_hash"] if "row_hash" in old_idx.columns else None
            new_h = new_idx.at[aid, "row_hash"] if "row_hash" in new_idx.columns else None

            # detect change
            if pd.isna(old_h) or pd.isna(new_h) or old_h != new_h:
                updated_ids.add(aid)
            else:
                unchanged_ids.add(aid)

        # all IDs to replace
        to_replace = inserted_ids | updated_ids

        # union columns (in case schema evolves)
        all_cols = sorted(set(df_old.columns).union(set(df_new.columns)))
        old_idx = old_idx.reindex(columns=all_cols)
        new_idx = new_idx.reindex(columns=all_cols)

        # build output: keep old rows except those replaced; add replacement rows from new
        out_idx = old_idx.drop(index=list(to_replace), errors="ignore")
        if to_replace:
            out_idx = pd.concat([out_idx, new_idx.loc[list(to_replace)]], axis=0)

        # reset index and drop old index
        out = out_idx.reset_index(drop=True)

        # stable ordering (by start_time desc if present)
        if "start_time" in out.columns:
            out["start_time"] = pd.to_datetime(out["start_time"], errors="coerce", utc=True)
            out = out.sort_values("start_time", ascending=False, na_position="last")

        # write out
        out.to_parquet(self.activities_path, index=False)

        # return summary
        return {
            "inserted": int(len(inserted_ids)),
            "updated": int(len(updated_ids)),
            "unchanged": int(len(unchanged_ids)),
            "total": int(len(out)),
        }

    # methods to get/set cursor
    def get_cursor(self) -> Dict[str, Any]:
        if not self.cursor_path.exists():
            return {}
        # load and return cursor json
        return json.loads(self.cursor_path.read_text(encoding="utf-8"))
    
    def set_cursor(self, cursor: Dict[str, Any]) -> None:
        self.cursor_path.write_text(json.dumps(cursor, indent=2, sort_keys=True), encoding="utf-8")

    # method to get current UTC time in ISO format
    @staticmethod
    def now_utc_iso() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()