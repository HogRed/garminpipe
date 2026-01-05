from __future__ import annotations

import pandas as pd


def clean_activities(df: pd.DataFrame) -> pd.DataFrame:
    """
    Opinionated cleaning:
    - ensures numeric cols
    - adds derived pace for run-like activities
    - adds week_start
    """
    if df.empty:
        return df.copy()

    out = df.copy()

    # Ensure datetime
    if "start_time" in out.columns:
        out["start_time"] = pd.to_datetime(out["start_time"], errors="coerce", utc=True)

    # Derived pace: seconds per km (for running-ish types)
    run_keys = {"running", "treadmill_running", "trail_running"}
    if "activity_type" in out.columns and "distance_m" in out.columns and "duration_s" in out.columns:
        is_run = out["activity_type"].isin(run_keys)
        km = out["distance_m"] / 1000.0
        out["avg_pace_s_per_km"] = pd.NA
        out.loc[is_run & (km > 0), "avg_pace_s_per_km"] = out.loc[is_run & (km > 0), "duration_s"] / km[is_run & (km > 0)]

    # Week start (Monday)
    if "start_time" in out.columns:
        # Week start (Monday), preserving tz-awareness (UTC)
        st = out["start_time"]
        
        # Ensure UTC tz-aware
        st = pd.to_datetime(st, utc=True, errors="coerce")
        out["week_start"] = (st - pd.to_timedelta(st.dt.weekday, unit="D")).dt.normalize()

    return out
