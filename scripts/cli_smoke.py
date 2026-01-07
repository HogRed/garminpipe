from datetime import date, timedelta
from garminpipe.clients.garth_client import GarthClient
from garminpipe.config import GarminPipeConfig  # adjust import if your config lives elsewhere

cfg = GarminPipeConfig()
client = GarthClient(session_dir=cfg.session_dir)

# resume session (or login via CLI first)
client.resume()

until = date.today()
start_date = until - timedelta(days=7)

batch = client.list_activities(start_date=start_date, end_date=until, start=0, limit=5)

print("Count:", len(batch))
print("Keys in first activity:", sorted(batch[0].keys()))
print("First activity raw dict:\n", batch[0])
