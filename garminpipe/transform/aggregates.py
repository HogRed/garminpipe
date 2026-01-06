from __future__ import annotations

import pandas as pd


def weekly_rollup(df: pd.DataFrame) -> pd.DataFrame:
    # return weekly aggregates of activities.
    if df.empty:
        # empty input -> empty output
        return df.copy()

    # require week_start column
    if "week_start" not in df.columns:
        raise ValueError("weekly_rollup expects a 'week_start' column. Run clean_activities() first.")

    # aggregate by week_start
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
    # derived columns
    agg["total_distance_km"] = (agg["total_distance_m"] / 1000.0).round(2)
    agg["total_duration_hr"] = (agg["total_duration_s"] / 3600.0).round(2)

    # convert kilometers to miles
    agg["total_distance_miles"] = (agg["total_distance_km"] * 0.621371).round(2)

    # combo time field wich has hours and minutes
    agg["total_duration_hr_min"] = agg["total_duration_s"].apply(
        lambda x: f"{int(x // 3600)}h {int((x % 3600) // 60)}m"
    )

    return agg

def weekly_rollup_by_type(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return weekly aggregates split by activity_type.

    Expects:
      - week_start (tz-aware datetime recommended; produced by clean_activities)
      - activity_type
      - activity_id, distance_m, duration_s, avg_hr_bpm, elevation_gain_m

    Output columns:
      week_start, activity_type, activities, total_distance_m, total_duration_s,
      avg_hr_bpm, elevation_gain_m, total_distance_km, total_duration_hr,
      total_distance_miles, total_duration_hr_min
    """
    # catching empty input and raising appropriate errors
    if df.empty:
        return df.copy()

    if "week_start" not in df.columns:
        raise ValueError("weekly_rollup_by_type expects a 'week_start' column. Run clean_activities() first.")

    if "activity_type" not in df.columns:
        raise ValueError("weekly_rollup_by_type expects an 'activity_type' column.")

    # avoid losing rows with missing activity_type
    d = df.copy() # copy

    d["activity_type"] = d["activity_type"].fillna("unknown").astype(str)

    # get weekly data by activity type
    agg = (
        d.groupby(["week_start", "activity_type"], as_index=False)
        .agg(
            activities=("activity_id", "count"),
            total_distance_m=("distance_m", "sum"),
            total_duration_s=("duration_s", "sum"),
            avg_hr_bpm=("avg_hr_bpm", "mean"),
            elevation_gain_m=("elevation_gain_m", "sum"),
        )
    )

    # derived columns
    agg["total_distance_km"] = (agg["total_distance_m"] / 1000.0).round(2)
    agg["total_duration_hr"] = (agg["total_duration_s"] / 3600.0).round(2)

    # convert kilometers to miles
    agg["total_distance_miles"] = (agg["total_distance_km"] * 0.621371).round(2)

    # duration string
    agg["total_duration_hr_min"] = agg["total_duration_s"].apply(
        lambda x: f"{int(x // 3600)}h {int((x % 3600) // 60)}m"
    )

    # nice ordering for display/plots
    agg = agg.sort_values(["activity_type", "week_start"])

    return agg