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

pipe = GarminPipe()
df = pipe.activities()
df_clean = pipe.clean(df)
weekly = pipe.weekly(df_clean)