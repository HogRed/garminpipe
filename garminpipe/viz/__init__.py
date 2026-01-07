from .weekly import (
    plot_weekly_metric, 
    plot_weekly_dashboard
)

from .intensity import (
    plot_weekly_hr,
    plot_speed_vs_hr_scatter,
    plot_pace_distribution,
    plot_weekly_pace_trend,
)

__all__ = [
    "plot_weekly_hr",
    "plot_speed_vs_hr_scatter",
    "plot_pace_distribution",
    "plot_weekly_pace_trend",
    "plot_weekly_metric",
    "plot_weekly_dashboard",
]