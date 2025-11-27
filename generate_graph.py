import json
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os

HISTORY_CSV_PATH = 'history_csv/graph_update_history.csv'
BUCKETS_JSON_PATH = 'buckets.json'
GRAPH_PATH = 'history_csv/update_history.png'

def update_history_and_generate_graph():
    # 1. Read buckets.json to get the "Total" amount
    total_amount = None
    if os.path.exists(BUCKETS_JSON_PATH):
        with open(BUCKETS_JSON_PATH, 'r') as f:
            buckets_data = json.load(f)     # TODO my json being a list of dicts is dumb. It should be a dict keyed by bucket name. Value is the same, just remove name TODO would need to change update logic as well
            total_amount = buckets_data[-1].get('amount')
    
    if total_amount is None:
        print(f"Warning: 'amount' not found in {BUCKETS_JSON_PATH}. Skipping history update and graph generation.")
        return

    # 2. Get the current date
    current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 3. Append to a CSV
    # Ensure the history_csv directory exists
    os.makedirs(os.path.dirname(HISTORY_CSV_PATH), exist_ok=True)

    history_data = []
    if os.path.exists(HISTORY_CSV_PATH):
        try:
            history_df = pd.read_csv(HISTORY_CSV_PATH)
            history_data = history_df.to_dict('records')
        except pd.errors.EmptyDataError:
            pass # File exists but is empty

    history_data.append({'Date': current_date, 'Total': total_amount})
    
    # Convert to DataFrame and save
    history_df = pd.DataFrame(history_data)
    history_df.to_csv(HISTORY_CSV_PATH, index=False)
    print(f"History updated in {HISTORY_CSV_PATH}")

    # 4. Generate the graph
    if not history_df.empty:
        history_df['Date'] = pd.to_datetime(history_df['Date'])
        
        plt.figure(figsize=(10, 6))
        plt.scatter(history_df['Date'], history_df['Total'])
        plt.xlabel('Date')
        plt.ylabel('Total Amount')
        plt.title('Total Amount Over Time')
        plt.grid(True)
        plt.tight_layout()

        # 5. Save the plot
        plt.savefig(GRAPH_PATH)
        print(f"Graph saved to {GRAPH_PATH}")
    else:
        print("No data in history to generate graph.")
