import argparse
import json
import sys
import csv
from datetime import datetime
from pathlib import Path
import shutil

HISTORY_DIR = Path("history_csv")
BACKUP_DIR = Path("backups")

DEFAULT_LOG_FILE = HISTORY_DIR / "withdraw_log.csv"
DEFAULT_BUCKET_FILE = Path("buckets.json")


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


def backup_buckets(buckets_path):
    """Create a timestamped backup of buckets.json."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_path = BACKUP_DIR / f"buckets_backup_{timestamp}.json"

    try:
        shutil.copy(buckets_path, backup_path)
        print(f"Backup created: {backup_path}")
    except FileNotFoundError:
        print(f"Error: Could not back up '{buckets_path}'. File not found.")
        sys.exit(1)


def withdraw_amount(data, bucket, amount):
    """Remove money from a single bucket and update the total."""
    valid_buckets = ["Savings", "Needs", "Wants"]

    if bucket not in valid_buckets:
        raise ValueError("Only 'Savings', 'Needs', or 'Wants' can be chosen as buckets.")

    bucket_obj = next((b for b in data if b["name"] == bucket), None)

    if bucket_obj is None:
        raise ValueError("Bucket not found in bucket file.")

    if bucket_obj["amount"] < amount:
        raise ValueError(f"Not enough funds in {bucket}.")

    # Deduct amount
    bucket_obj["amount"] -= amount

    # Update total
    total = sum(next(b for b in data if b["name"] == name)["amount"]
                for name in valid_buckets)

    total_obj = next((b for b in data if b["name"] == "Total"), None)
    if total_obj:
        total_obj["amount"] = total

    return data


def log_withdrawal(bucket, amount, reason, log_path):
    """Log a single-bucket withdrawal to CSV."""
    timestamp = datetime.now().isoformat()

    # Ensure log directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)

    write_header = not log_path.exists()

    with open(log_path, "a", newline="") as file:
        writer = csv.writer(file)

        if write_header:
            writer.writerow(["timestamp", "bucket", "amount", "reason"])

        writer.writerow([timestamp, bucket, amount, reason])


def main():
    parser = argparse.ArgumentParser(
        description="Withdraw money from a bucket with a reason (with automatic backup)."
    )
    parser.add_argument("bucket", help="Bucket to withdraw from (Savings, Needs, Wants)")
    parser.add_argument("amount", type=float, help="Amount to withdraw")
    parser.add_argument("reason", help="Explanation for the withdrawal")
    parser.add_argument("--buckets", default=DEFAULT_BUCKET_FILE)
    parser.add_argument("--log", default=DEFAULT_LOG_FILE)

    args = parser.parse_args()

    # --- BACKUP FIRST ---
    backup_buckets(args.buckets)

    # Load data
    data = load_buckets(args.buckets)

    # Perform withdrawal
    try:
        withdraw_amount(data, args.bucket, args.amount)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Log to CSV
    log_withdrawal(args.bucket, args.amount, args.reason, Path(args.log))

    # Save updated buckets
    save_buckets(args.buckets, data)

    # Print updated state
    print("\nWithdrawal complete.\nUpdated bucket amounts:")
    for bucket in ["Savings", "Needs", "Wants", "Total"]:
        amt = next(b["amount"] for b in data if b["name"] == bucket)
        print(f"{bucket}: {amt}")


if __name__ == "__main__":
    main()


## TODO add everything to a gitignore and make templates for history, buckets