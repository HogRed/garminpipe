from __future__ import annotations

from typing import Optional, Tuple

import pandas as pd

# try to install mpl
try:
    import matplotlib.pyplot as plt
except ImportError as e:  # pragma: no cover
    raise ImportError(
        "matplotlib is required for plotting. Install with: pip install 'garminpipe[viz]'"
    ) from e

# ensure week_start is datetime with UTC tz
def _ensure_datetime(weekly: pd.DataFrame) -> pd.DataFrame:
    out = weekly.copy()
    out["week_start"] = pd.to_datetime(out["week_start"], errors="coerce", utc=True)
    out = out.sort_values("week_start")
    return out

def plot_weekly_metric(
    weekly: pd.DataFrame,
    metric: str = "total_distance_miles",
    title: Optional[str] = None,
    ax=None,
) -> Tuple["plt.Figure", "plt.Axes"]:
    """
    Plot one weekly metric as a line chart.

    Parameters:
    weekly : pd.DataFrame
        Output of weekly_rollup().
    metric : str
        Column to plot, e.g. total_distance_miles, total_duration_hr, activities.
    title : str | None
        Plot title. If None, a sensible default is chosen.
    ax : matplotlib Axes | None
        Provide an axes to draw on; if None a new figure is created.
    """
    if weekly.empty:
        raise ValueError("weekly dataframe is empty")

    if "week_start" not in weekly.columns:
        raise ValueError("weekly must contain 'week_start'")

    if metric not in weekly.columns:
        raise ValueError(f"weekly does not contain metric '{metric}'")

    # ensure week_start is datetime
    w = _ensure_datetime(weekly)

    if ax is None:
        fig, ax = plt.subplots()
    else:
        fig = ax.figure

    # facet plot to be based on activity type (run, walk, etc.)
    grouped = w.groupby("activity_type") if "activity_type" in w.columns else [(None, w)]

    # plot each activity type on the same plot, each with their own color
    for atype, df_atype in grouped:
        label = atype if atype is not None else "all"
        ax.plot(df_atype["week_start"], df_atype[metric], marker="o", label=label)
    ax.set_xlabel("Week starting")
    ax.set_ylabel(metric.replace("_", " "))
    ax.grid(True, alpha=0.3)
    if title is None:
        title = f"Weekly {metric.replace('_', ' ')}"
    ax.set_title(title)
    if "activity_type" in w.columns:
        ax.legend(title="Activity type")
    fig.autofmt_xdate()

            

    return fig, ax


def plot_weekly_dashboard(
    weekly: pd.DataFrame,
    distance_col: str = "total_distance_miles",
    duration_col: str = "total_duration_hr",
    count_col: str = "activities",
    title: str = "Weekly training summary",
) -> "plt.Figure":
    """
    Creates a simple 3-panel dashboard: distance, duration, activity count.
    Returns a matplotlib Figure.
    """
    if weekly.empty:
        raise ValueError("weekly dataframe is empty")

    w = _ensure_datetime(weekly)

    fig, axes = plt.subplots(nrows=3, ncols=1, sharex=True, figsize=(10, 8))

    axes[0].plot(w["week_start"], w[distance_col])
    axes[0].set_ylabel(distance_col.replace("_", " "))
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(w["week_start"], w[duration_col])
    axes[1].set_ylabel(duration_col.replace("_", " "))
    axes[1].grid(True, alpha=0.3)

    axes[2].plot(w["week_start"], w[count_col])
    axes[2].set_ylabel(count_col.replace("_", " "))
    axes[2].grid(True, alpha=0.3)

    axes[0].set_title(title)
    fig.autofmt_xdate()

    return fig

def plot_weekly_by_type(
    weekly_by_type: pd.DataFrame,
    metric: str = "total_distance_miles",
    title: Optional[str] = None,
    ax=None,
) -> Tuple["plt.Figure", "plt.Axes"]:
    """
    Plot one weekly metric split by activity type as a line chart.

    Parameters:
    weekly_by_type : pd.DataFrame
        Output of weekly_rollup_by_type().
    metric : str
        Column to plot, e.g. total_distance_miles, total_duration_hr, activities.
    title : str | None
        Plot title. If None, a sensible default is chosen.
    ax : matplotlib Axes | None
        Provide an axes to draw on; if None a new figure is created.
    """
    if weekly_by_type.empty:
        raise ValueError("weekly_by_type dataframe is empty")

    if "week_start" not in weekly_by_type.columns:
        raise ValueError("weekly_by_type must contain 'week_start'")

    if "activity_type" not in weekly_by_type.columns:
        raise ValueError("weekly_by_type must contain 'activity_type'")

    if metric not in weekly_by_type.columns:
        raise ValueError(f"weekly_by_type does not contain metric '{metric}'")

    # ensure week_start is datetime
    w = _ensure_datetime(weekly_by_type)

    if ax is None:
        fig, ax = plt.subplots()
    else:
        fig = ax.figure

    # plot to be based on activity type (run, walk, etc.)
    grouped = w.groupby("activity_type")

    # plot each activity type on the same plot, each with their own color
    for atype, df_atype in grouped:
        label = atype if atype is not None else "all"
        ax.plot(df_atype["week_start"], df_atype[metric], marker="o", label=label)

    ax.set_xlabel("Week starting")
    ax.set_ylabel(metric.replace("_", " "))
    ax.grid(True, alpha=0.3)
    if title is None:
        title = f"Weekly {metric.replace('_', ' ')} by activity type"
    ax.set_title(title)
    ax.legend(title="Activity type")
    fig.autofmt_xdate()

    return fig, ax

def plot_weekly_hr_zone_stack(
    weekly_zones: pd.DataFrame,
    normalize: bool = False,
    ax=None,
    title: Optional[str] = None,
) -> Tuple["plt.Figure", "plt.Axes"]:
    """
    Stacked bar chart of HR zone minutes (or percent) by week.

    weekly_zones: output of weekly_hr_zone_rollup()
    normalize: if True, plot zone%i_pct (0-100). else plot zone%i_min.
    """
    # error handling
    if weekly_zones.empty:
        raise ValueError("weekly_zones dataframe is empty")

    if "week_start" not in weekly_zones.columns:
        raise ValueError("weekly_zones must contain 'week_start'")

    w = weekly_zones.copy() # copy

    # ensure week_start is datetime
    w["week_start"] = pd.to_datetime(w["week_start"], errors="coerce", utc=True)
    w = w.sort_values("week_start")
    x = w["week_start"].dt.tz_convert(None)

    # determine metric columns to plot
    metric_cols = [f"zone{i}_{'pct' if normalize else 'min'}" for i in range(1, 6)]
    # see if missing cols; if so, error
    missing = [c for c in metric_cols if c not in w.columns]
    if missing:
        raise ValueError(f"Missing expected columns for plot: {missing}")

    # if no ax, create new figure
    if ax is None:
        fig, ax = plt.subplots()
    else:
        fig = ax.figure

    # bottom is for stacking
    bottom = None

    # plot each zone
    for c in metric_cols:
        y = w[c].astype(float).fillna(0.0)
        if bottom is None:
            ax.bar(x, y, label=c) # plot bar
            bottom = y # set bottom for next
        else:
            ax.bar(x, y, bottom=bottom, label=c, width=6) # plot bar stacked on previous
            bottom = bottom + y # update bottom

    # labels and title
    ax.set_xlabel("Week start")
    ax.set_ylabel("Percent of zone time" if normalize else "Minutes in HR zones")
    ax.set_title(title or ("Weekly HR zone distribution (%)" if normalize else "Weekly HR zone time (minutes)"))
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper left", ncols=2, fontsize="small")
    fig.autofmt_xdate()

    return fig, ax