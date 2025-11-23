## TODO add code to just copy the actual buckets.json
from pathlib import Path
import json
from datetime import datetime
import csv

simbucket = Path("buckets.json")

realbucket = Path("../buckets.json")

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

historycsv = Path("history_csv") / "sync_log.csv"

backuppath = Path("backups") / f"backup_{timestamp}.json"
backuppath.parent.mkdir(parents=True, exist_ok=True)

## load up the sim and real
with open(simbucket, 'r') as f:
    sim = json.load(f)

with open(realbucket, 'r') as f:
    real = json.load(f)

## back up the sim
with open(backuppath, 'w') as f:
    json.dump(sim, f, indent=4)

historyExists = historycsv.exists()

## add note to history csv
with open(historycsv, 'a', newline='') as f:
    writer = csv.writer(f)
    if not historyExists:
        writer.writerow(["sync_timestamp"])
    writer.writerow([timestamp])

## overwrite sim w real
with open(simbucket, 'w') as f:
    json.dump(real, f, indent=4)