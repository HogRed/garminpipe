from __future__ import annotations

from typing import Optional, Tuple

import pandas as pd

try:
    import matplotlib.pyplot as plt
except ImportError as e:  # pragma: no cover
    raise ImportError("matplotlib is required for plotting. Install with: pip install 'garminpipe[viz]'") from e


def _x_datetime(series: pd.Series) -> pd.Series:
    x = pd.to_datetime(series, errors="coerce", utc=True)
    return x.dt.tz_convert(None)


def plot_weekly_hr(
    weekly_hr: pd.DataFrame,
    ax=None,
    title: str = "Weekly heart rate (avg & max)",
) -> Tuple["plt.Figure", "plt.Axes"]:
    """
    Lines: avg_hr_mean_bpm and max_hr_max_bpm.
    """
    if weekly_hr.empty:
        raise ValueError("weekly_hr is empty")

    required = {"week_start", "avg_hr_mean_bpm", "max_hr_max_bpm"}
    missing = sorted(required - set(weekly_hr.columns))
    if missing:
        raise ValueError(f"plot_weekly_hr missing columns: {missing}")

    w = weekly_hr.copy()
    x = _x_datetime(w["week_start"])

    if ax is None:
        fig, ax = plt.subplots()
    else:
        fig = ax.figure

    ax.plot(x, w["avg_hr_mean_bpm"], label="Avg HR (mean)")
    ax.plot(x, w["max_hr_max_bpm"], label="Max HR (max)")
    ax.set_xlabel("Week start")
    ax.set_ylabel("BPM")
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.autofmt_xdate()
    return fig, ax


def plot_speed_vs_hr_scatter(
    df: pd.DataFrame,
    ax=None,
    title: str = "Speed vs Avg HR (runs)",
) -> Tuple["plt.Figure", "plt.Axes"]:
    """
    Scatter: speed_mph (x) vs avg_hr_bpm (y).
    Expects add_intensity_metrics() was applied so speed_mph exists.
    """
    if df.empty:
        raise ValueError("df is empty")

    required = {"speed_mph", "avg_hr_bpm"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"plot_speed_vs_hr_scatter missing columns: {missing}")

    d = df.copy()
    d["speed_mph"] = pd.to_numeric(d["speed_mph"], errors="coerce")
    d["avg_hr_bpm"] = pd.to_numeric(d["avg_hr_bpm"], errors="coerce")

    d = d.dropna(subset=["speed_mph", "avg_hr_bpm"])
    if d.empty:
        raise ValueError("No rows with non-null speed_mph and avg_hr_bpm")

    if ax is None:
        fig, ax = plt.subplots()
    else:
        fig = ax.figure

    ax.scatter(d["speed_mph"], d["avg_hr_bpm"])
    ax.set_xlabel("Speed (mph)")
    ax.set_ylabel("Avg HR (bpm)")
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    return fig, ax


def plot_pace_distribution(
    df: pd.DataFrame,
    ax=None,
    title: str = "Pace distribution (min/mile)",
    bins: int = 30,
) -> Tuple["plt.Figure", "plt.Axes"]:
    """
    Histogram of pace_min_per_mile.
    Expects add_intensity_metrics() was applied so pace_min_per_mile exists.
    """
    if df.empty:
        raise ValueError("df is empty")

    if "pace_min_per_mile" not in df.columns:
        raise ValueError("plot_pace_distribution expects pace_min_per_mile. Run add_intensity_metrics() first.")

    d = df.copy()
    d["pace_min_per_mile"] = pd.to_numeric(d["pace_min_per_mile"], errors="coerce")
    d = d.dropna(subset=["pace_min_per_mile"])

    # optional: filter extreme outliers
    d = d[(d["pace_min_per_mile"] > 3) & (d["pace_min_per_mile"] < 25)]

    if d.empty:
        raise ValueError("No valid pace values to plot after filtering")

    if ax is None:
        fig, ax = plt.subplots()
    else:
        fig = ax.figure

    ax.hist(d["pace_min_per_mile"], bins=bins)
    ax.set_xlabel("Pace (min/mile)")
    ax.set_ylabel("Count")
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    return fig, ax


def plot_weekly_pace_trend(
    weekly_pace: pd.DataFrame,
    ax=None,
    title: str = "Weekly median pace (min/mile)",
) -> Tuple["plt.Figure", "plt.Axes"]:
    if weekly_pace.empty:
        raise ValueError("weekly_pace is empty")

    required = {"week_start", "pace_median_min_per_mile"}
    missing = sorted(required - set(weekly_pace.columns))
    if missing:
        raise ValueError(f"plot_weekly_pace_trend missing columns: {missing}")

    w = weekly_pace.copy()
    x = _x_datetime(w["week_start"])

    if ax is None:
        fig, ax = plt.subplots()
    else:
        fig = ax.figure

    ax.plot(x, w["pace_median_min_per_mile"])
    ax.set_xlabel("Week start")
    ax.set_ylabel("Median pace (min/mile)")
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    fig.autofmt_xdate()

    # Optional: invert y-axis so "faster" (lower pace) trends upward
    ax.invert_yaxis()

    return fig, ax