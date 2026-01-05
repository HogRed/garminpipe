# garminpipe

Sync Garmin Connect activities to a local Parquet file and provide analysis-friendly helpers.

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