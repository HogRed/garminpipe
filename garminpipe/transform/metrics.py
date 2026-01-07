from __future__ import annotations

import pandas as pd
import numpy as np

M_PER_MILE = 1609.344

def weekly_hr_rollup(df: pd.DataFrame) -> pd.DataFrame:
    """
    Weekly HR rollup for intensity plots.

    Expects:
      - week_start
      - avg_hr_bpm
      - max_hr_bpm

    Returns:
      week_start, avg_hr_mean_bpm, max_hr_mean_bpm, max_hr_max_bpm
    """
    if df.empty:
        return df.copy()

    if "week_start" not in df.columns:
        raise ValueError("weekly_hr_rollup expects a 'week_start' column. Run clean_activities() first.")

    d = df.copy()
    for c in ["avg_hr_bpm", "max_hr_bpm"]:
        if c in d.columns:
            d[c] = pd.to_numeric(d[c], errors="coerce")

    agg = (
        d.groupby("week_start", as_index=False)
        .agg(
            avg_hr_mean_bpm=("avg_hr_bpm", "mean"),
            max_hr_mean_bpm=("max_hr_bpm", "mean"),
            max_hr_max_bpm=("max_hr_bpm", "max"),
        )
    )

    # keep tidy and stable
    return agg.sort_values("week_start")


def weekly_pace_rollup(df: pd.DataFrame) -> pd.DataFrame:
    """
    Weekly pace rollup.

    Expects:
      - week_start
      - pace_min_per_mile (use add_intensity_metrics first)

    Returns:
      week_start, pace_median_min_per_mile, pace_mean_min_per_mile
    """
    if df.empty:
        return df.copy()

    if "week_start" not in df.columns:
        raise ValueError("weekly_pace_rollup expects a 'week_start' column. Run clean_activities() first.")

    if "pace_min_per_mile" not in df.columns:
        raise ValueError("weekly_pace_rollup expects 'pace_min_per_mile'. Run add_intensity_metrics() first.")

    d = df.copy()
    d["pace_min_per_mile"] = pd.to_numeric(d["pace_min_per_mile"], errors="coerce")

    # Optional: drop extreme paces that are likely GPS/device artifacts
    d = d[(d["pace_min_per_mile"] > 3) & (d["pace_min_per_mile"] < 25)]

    agg = (
        d.groupby("week_start", as_index=False)
        .agg(
            pace_median_min_per_mile=("pace_min_per_mile", "median"),
            pace_mean_min_per_mile=("pace_min_per_mile", "mean"),
        )
    )
    return agg.sort_values("week_start")

def add_intensity_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds derived intensity metrics suitable for plotting.

    Requires:
      - distance_m
      - duration_s

    Optionally uses:
      - avg_hr_bpm
      - max_hr_bpm

    Adds:
      - distance_miles
      - duration_min
      - speed_mph
      - pace_min_per_mile
    """
    if df.empty:
        return df.copy()

    out = df.copy()

    # Ensure numeric
    for c in ["distance_m", "duration_s", "avg_hr_bpm", "max_hr_bpm"]:
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce")

    out["distance_miles"] = out["distance_m"] / M_PER_MILE
    out["duration_min"] = out["duration_s"] / 60.0

    # speed (mph): miles / hours
    hours = out["duration_s"] / 3600.0
    out["speed_mph"] = np.where(hours > 0, out["distance_miles"] / hours, np.nan)

    # pace (min/mile): minutes / miles
    out["pace_min_per_mile"] = np.where(out["distance_miles"] > 0, out["duration_min"] / out["distance_miles"], np.nan)

    # Clean up degenerate rows
    out.loc[out["distance_miles"] <= 0, ["speed_mph", "pace_min_per_mile"]] = np.nan

    return out