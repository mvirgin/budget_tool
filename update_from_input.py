## I need to define the buckets - maybe as json?
## I need to import two csvs per update - checkings and savings
    ## I guess I can just smash the csv's together and sort by date to make it easier to digest in my brain
## I need to log dates so transactions dont double up - maybe every update - gather all transactions with the most recent date and put them in a log
    ## Then come next update skip the transactions that match those rows recorded above

## Savings should represent my savings bucket and Checking should be split between Needs/Wants?
import csv
from pathlib import Path
from typing import Dict, Any
import json
import shutil
from datetime import datetime

## TODO I should probably bite the bullet and add unique IDs to each row
## what if I buy two identical products from amazon - rows would be identical no? But I only block if they're in prior history
## so unless I update this twice in one day after making two+ identical purchases so that one+ is in history, I'm good

def load_csv(path: str | Path) -> list[Dict[str, Any]]:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = []
        ## eliminate trailing commas
        for row in reader:
            # Remove any keys that are empty strings
            clean_row = {k: v for k, v in row.items() if k}
            rows.append(clean_row)
        return rows
    

def merge_csvs(csv_a: str | Path, csv_b: str | Path) -> list[Dict[str, Any]]:
    rows = load_csv(csv_a) + load_csv(csv_b)
    return rows

def get_amount_from_row(row: dict) -> float:
    """
    Converts a CSV row with Debit/Credit into a signed float.
    Debit = negative
    Credit = positive
    Empty = 0
    """
    debit = row.get("Debit", "").strip()
    credit = row.get("Credit", "").strip()

    if debit:
        return float(debit.replace("$", "").replace(",", ""))
    if credit:
        return float(credit.replace("$", "").replace(",", ""))

    return debit | credit

def matches_pattern(text: str, patterns: list[str]) -> bool:
        """Case-insensitive substring search."""
        t = text.lower()
        return any(p.lower() in t for p in patterns)

bucketHitDict = {
    "all": "SNW",
    "Savings": "S",
    "Needs": "N",
    "Wants": "W",
    "SN": "SN",     ## these 3 are probably unneeded
    "SW": "SW",
    "NW": "NW"
}

def update_buckets(history_csv_path, buckets_dict, rows):
    prior_history = load_csv(history_csv_path)
    file_exists = history_csv_path.exists() and history_csv_path.stat().st_size > 0
    modrow = rows[0]
    newCat = "BucketsHit"
    modrow[newCat] = "S,N,W"
    total_added = 0

    with open(history_csv_path, 'a', newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=modrow.keys())
        if not file_exists:
            writer.writeheader()

        ## iterate over rows, applying each row to its bucket
        for row in rows:
            desc = row["Description"]
            amount = get_amount_from_row(row)
            total_added += amount

            ## handle case where row represents paycheck
            paycheck_bucket = buckets_dict.get("Paycheck")
            if paycheck_bucket: # should always exist but just in case
                patterns = paycheck_bucket.get("patterns",[])
                if matches_pattern(desc, patterns) and amount > 0:  # make sure paycheck isn't negative ig?
                    for bucket_name, percent in paycheck_bucket["split"].items():
                        if bucket_name not in buckets_dict:
                            raise ValueError(
                                f"Bucket '{bucket_name}' missing from buckets.json!"
                            )
                        somerow = row
                        somerow[newCat] = bucketHitDict["all"]
                        if somerow not in prior_history:
                            buckets_dict[bucket_name]["amount"] += amount*percent

                    if somerow not in prior_history:   
                        writer.writerow(somerow)    ## this was the cause of the duplication - writing row for each bucket
                        
                    continue    # skip the rest of this iteration, we've decided what to do with this row

            ## handle other cases
            matched = False
            for bucket_name, info in buckets_dict.items():
                if bucket_name == "paycheck":
                    continue    # skip this iteration, this is handled above

                patterns = info.get("patterns", [])

                if matches_pattern(desc, patterns):
                    somerow = row   # TODO this is modifying row becuz this a reference? Doesn't matter - I was preserving row for no real reason really
                    somerow[newCat] = bucketHitDict[bucket_name]
                    if somerow not in prior_history:
                        writer.writerow(somerow)
                        info["amount"] += amount
                    matched = True
                    break   # only 1 row can affect 1 bucket

            ## default case - no matches
            if not matched:
                somerow = row   ## TODO code dupe 3x is dumb
                somerow[newCat] = bucketHitDict["Wants"]
                if somerow not in prior_history:
                    writer.writerow(somerow)
                    buckets_dict["Wants"]["amount"] += amount

    total = buckets_dict["Wants"]["amount"] + buckets_dict["Needs"]["amount"] + buckets_dict["Savings"]["amount"]
    buckets_dict["Total"]["amount"] = total
    print("Total Added:", total_added)

def sort_by_date(rows):
    return sorted(
        rows,
        key=lambda r: datetime.strptime(r["Date"], "%m/%d/%Y")
    )

if __name__ == "__main__":
    INPUT_DIR = Path("input_csvs")
    HISTORY_DIR = Path("history_csv")
    BUCKETS_JSON = Path("buckets.json")
    BACKUP_DIR = Path("backups")

    history_backup = BACKUP_DIR / "history.csv"
    export1_backup = BACKUP_DIR / "export1.csv"
    export2_backup = BACKUP_DIR / "export2.csv"
    buckets_backup = BACKUP_DIR / "buckets.json"

    history_csv_path = HISTORY_DIR / "history.csv"

    ## backup history b4 we start

    # Ensure backup folder exists
    BACKUP_DIR.mkdir(exist_ok=True)

    # Copy history -> backup, overwriting any existing backup
    shutil.copy(history_csv_path, history_backup)
    # backup current bucket before we update
    shutil.copy(BUCKETS_JSON, buckets_backup)

    # Load JSON into a list of dicts
    with open(BUCKETS_JSON, "r", encoding="utf-8") as f:
        buckets_list = json.load(f)  # List[Dict]

    # Convert to dict keyed by name 
    buckets_dict = {bucket["name"]: bucket for bucket in buckets_list}

    csvs = list(INPUT_DIR.glob("*.csv"))

    # 2. Load + combine CSVs
    if len(csvs) == 2:
        shutil.copy(csvs[0], export1_backup)
        shutil.copy(csvs[1], export2_backup) 
        rows = sort_by_date(merge_csvs(csvs[0], csvs[1]))
    elif len(csvs) == 1:
        shutil.copy(csvs[0], export1_backup) 
        rows = sort_by_date(load_csv(csvs[0]))
    else:
        raise ValueError(f"Expected 1 or 2 input files, not {len(csvs)}")

    update_buckets(history_csv_path, buckets_dict, rows)
            ## maintain a csv that records each row with an extra column telling what bucket(s) that row hit
            ## should not overlap is overlapping is handled correctly with the most recent transactions thing. Or this could BE the most recent transactions thing / serve the same role

    ## save new, updated buckets
    with open(BUCKETS_JSON, "w", encoding="utf-8") as f:
        # Convert dict back to a list for your JSON format
        json_list = list(buckets_dict.values())
        json.dump(json_list, f, indent=4)

    ## clear input csvs
    [p.unlink() for p in csvs]     ## TODO add an if success then delete?


# TODO add rebalancing tools so I can move money from one bucket to another (total balance stays the same)
# TODO set up lm studio to act like claude and look at this codebase so I can add comments and things
## TODO history.csv should be copied into backups after every run with a name that has the date/TS of the run

def combine_csvs(csv1, csv2):
    pass

def main():
    pass
    ## ingest csvs - names given via command line - they'll be in a subfolder of this directory
    ## combine them into a single csv via helper func (or probably a dict)
    ## delete input csvs
    ## make sure to check 'most recent transactions' csv to avoid overlap
    ## iterate over csv, modifying buckets.json as we go - changing the "amount" field for each transaction's bucket
        ## paychecks need to be split across buckets 60 needs 30 savings 10 wants
        ## use regex or smthn to determine which transactions go in which buckets? - maybe that goes in the buckets json
        ## if unkown, default to modifying the wants bucket
        ## when done put clear most recent transactions csv and put new most recents in


## long term:
## host the buckets.json file somewhere so I can access from my phone anytime
## maintain a 2nd, "guesstimate" version where user can directly specify which bucket they want to hit and put in a +/- amount
## compare this with the actual the next time it is updated to see how accurate it is