import argparse
import json
import sys
import csv
from datetime import datetime
from pathlib import Path
import shutil

HISTORY_DIR = Path("history_csv")
BACKUP_DIR = Path("backups")

DEFAULT_LOG_FILE = HISTORY_DIR / "transfer_log.csv"
DEFAULT_BUCKET_FILE = Path("buckets.json")
DEFAULT_BACKUP_BUCKET_FILE = BACKUP_DIR / "buckets_transfer_ver.json"

def load_buckets(path):
    """Load bucket data from JSON file."""
    try:
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Bucket file '{path}' not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Bucket file '{path}' is not valid JSON.")
        sys.exit(1)


def save_buckets(path, data):
    """Write updated bucket data back to JSON file."""
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


def transfer_amount(data, from_bucket, to_bucket, amount):
    valid_buckets = ["Savings", "Needs", "Wants"]

    if from_bucket not in valid_buckets or to_bucket not in valid_buckets:
        raise ValueError("Only 'Savings', 'Needs', or 'Wants' can be chosen as buckets.")

    if from_bucket == to_bucket:
        raise ValueError("Source and destination buckets must be different.")

    from_obj = next((b for b in data if b["name"] == from_bucket), None)
    to_obj = next((b for b in data if b["name"] == to_bucket), None)

    if from_obj is None or to_obj is None:
        raise ValueError("Bucket not found in bucket file.")

    if from_obj["amount"] < amount:
        raise ValueError(f"Not enough funds in {from_bucket}.")

    # Transfer
    from_obj["amount"] -= amount
    to_obj["amount"] += amount

    # Update the total
    total = sum(next(b for b in data if b["name"] == bucket)["amount"]
                for bucket in valid_buckets)

    total_obj = next((b for b in data if b["name"] == "Total"), None)
    if total_obj:
        total_obj["amount"] = total

    return data


def log_transfer(from_bucket, to_bucket, amount, reason, log_path):
    timestamp = datetime.now().isoformat()

    write_header = False
    try:
        with open(log_path, "r"):
            pass
    except FileNotFoundError:
        write_header = True

    with open(log_path, "a", newline="") as file:
        writer = csv.writer(file)

        if write_header:
            writer.writerow(["timestamp", "from_bucket", "to_bucket", "amount", "reason"])

        writer.writerow([timestamp, from_bucket, to_bucket, amount, reason])


def main():
    parser = argparse.ArgumentParser(
        description="Transfer money between Savings, Needs, and Wants with a reason."
    )
    parser.add_argument("from_bucket")
    parser.add_argument("to_bucket")
    parser.add_argument("amount", type=float)
    parser.add_argument("reason")
    parser.add_argument("--buckets", default=DEFAULT_BUCKET_FILE)
    parser.add_argument("--log", default=DEFAULT_LOG_FILE)

    args = parser.parse_args()

    # Load data
    data = load_buckets(args.buckets)

    # back it up before we do anything
    shutil.copy(args.buckets, DEFAULT_BACKUP_BUCKET_FILE)

    # Perform transfer
    try:
        transfer_amount(data, args.from_bucket, args.to_bucket, args.amount)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Log to CSV
    log_transfer(args.from_bucket, args.to_bucket, args.amount, args.reason, args.log)

    # Save updated JSON
    save_buckets(args.buckets, data)

    # Print updated state
    print("\nTransfer complete.\nUpdated bucket amounts:")
    for bucket in ["Savings", "Needs", "Wants", "Total"]:
        amt = next(b["amount"] for b in data if b["name"] == bucket)
        print(f"{bucket}: {amt}")


if __name__ == "__main__":
    main()