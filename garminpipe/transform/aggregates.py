from __future__ import annotations

import pandas as pd


def weekly_rollup(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    if "week_start" not in df.columns:
        raise ValueError("weekly_rollup expects a 'week_start' column. Run clean_activities() first.")

    agg = (
        df.groupby("week_start", as_index=False)
        .agg(
            activities=("activity_id", "count"),
            total_distance_m=("distance_m", "sum"),
            total_duration_s=("duration_s", "sum"),
            avg_hr_bpm=("avg_hr_bpm", "mean"),
            elevation_gain_m=("elevation_gain_m", "sum"),
        )
    )
    agg["total_distance_km"] = (agg["total_distance_m"] / 1000.0).round(2)
    agg["total_duration_hr"] = (agg["total_duration_s"] / 3600.0).round(2)
    return agg
