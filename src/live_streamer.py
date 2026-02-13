import pandas as pd
import time
import random
import os
from datetime import datetime

# Configuration
STREAM_DIR = "raw_data/stream"
STREAM_FILE = os.path.join(STREAM_DIR, "live_stream.csv")
REFRESH_RATE = 1.0  # Seconds between each data point

def initialize_stream():
    """Ensures the directory and file exist with proper headers."""
    if not os.path.exists(STREAM_DIR):
        os.makedirs(STREAM_DIR)
        print(f"📁 Created directory: {STREAM_DIR}")

    # Create file with headers if it doesn't exist
    if not os.path.exists(STREAM_FILE):
        df = pd.DataFrame(columns=["timestamp", "sales", "inventory_level", "store_id"])
        df.to_csv(STREAM_FILE, index=False)
        print(f"📄 Initialized stream file: {STREAM_FILE}")

def generate_live_data():
    now = datetime.now().strftime("%H:%M:%S")
    return pd.DataFrame([{
        "timestamp": now,                # Column 1
        "sales": random.randint(100, 1000), # Column 2
        "inventory": random.randint(10, 50), # Column 3
        "store_id": f"ST_{random.randint(1, 5):03d}" # Column 4
    }])

def start_streaming():
    """Main loop to continuously append data."""
    initialize_stream()
    print(f"🚀 Streaming started... Press Ctrl+C to stop.")
    print(f"📡 Writing to {STREAM_FILE}")
    
    try:
        while True:
            new_row = generate_live_data()
            
            # Append mode ('a'), no header, no index
            new_row.to_csv(STREAM_FILE, mode='a', header=False, index=False)
            
            # Print to console for visibility
            ts = new_row["timestamp"].iloc[0]
            val = new_row["sales"].iloc[0]
            print(f"[{ts}] 🛒 Sale recorded: ${val}")
            
            time.sleep(REFRESH_RATE)
            
    except KeyboardInterrupt:
        print("\n🛑 Stream stopped by user.")

if __name__ == "__main__":
    start_streaming()