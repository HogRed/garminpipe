# garminpipe

Sync Garmin Connect activities to a local Parquet file and provide analysis-friendly helpers. This project is still in the early stages, so all functionality is not there yet.

## Install (dev)
pip install -e .

## Authenticate
garminpipe auth login --email you@example.com

## Sync
garminpipe sync

## Use in Python
```python
from garminpipe import GarminPipe

pipe = GarminPipe() # establish connection to Garmin
df = pipe.activities() # get data
df_new = pipe.sync() # sync / update
df_clean = pipe.clean(df) # clean fields
weekly = pipe.weekly() # get weekly aggregated data
weekly_by_type = pipe.weekly_by_type() # get weekly data by activity type

# example plot
fig1, ax1 = plot_weekly_metric(
        weekly,
        metric="total_distance_miles",
        title="Weekly distance (miles)"
    )