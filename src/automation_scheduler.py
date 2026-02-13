import schedule
import time
import sys
import os
import functools
import polars as pl
from datetime import datetime

# --- CONFIGURATION ---
# Add the 'src' directory to the python path so we can import our modules
sys.path.append(os.path.join(os.getcwd(), "src"))

try:
    # Import specific functions to separate "Fast" (Stream) from "Slow" (Batch)
    # We assume generate_mock_data has a 'main' function for batch, and 'generate_web_logs' for stream
    from generate_mock_data import generate_web_logs, main as generate_full_batch
    from etl_pipeline import process_web_logs, process_dimensions, process_facts
except ImportError as e:
    print(f"❌ Error importing modules: {e}")
    print("Make sure you are running this script from the project root folder.")
    sys.exit(1)

# --- RESILIENCE LAYER: AUTOMATIC RETRIES ---
# Problem Statement Requirement: "include automatic retries if a connection fails"
def with_retries(max_attempts=3, delay=5):
    """
    A decorator that wraps a function. If the function fails, it waits 'delay' seconds
    and tries again, up to 'max_attempts'.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    print(f"⚠️ [{timestamp}] Job Failed (Attempt {attempt}/{max_attempts}). Error: {e}")
                    
                    if attempt == max_attempts:
                        print(f"❌ [{timestamp}] CRITICAL: Job failed after {max_attempts} attempts. Skipping...")
                        return None # Graceful exit, don't crash the scheduler
                    
                    print(f"   ... Retrying in {delay} seconds ...")
                    time.sleep(delay)
        return wrapper
    return decorator

# --- PIPELINE: FAST LANE (Near Real-Time) ---
# Goal: Process Web Logs frequently (e.g., every 30 seconds)
@with_retries(max_attempts=3)
def run_real_time_sync():
    print(f"\n⚡ [Real-Time] Syncing Web Events at {datetime.now().strftime('%H:%M:%S')}...")
    
    # 1. Simulate data arriving (Generation)
    # We need to read existing Customers/Products to generate valid logs
    # This simulates the "Live Website" sending data based on existing catalog
    cust_path = os.path.join("raw_data", "dim_customers.csv")
    prod_path = os.path.join("raw_data", "dim_products.csv")
    
    if not os.path.exists(cust_path) or not os.path.exists(prod_path):
        print("   ⚠️ Base data missing. Waiting for Batch Run first.")
        return

    # Load IDs quickly using Polars
    dim_customers = pl.read_csv(cust_path)
    product_ids = pl.read_csv(prod_path)["product_id"].to_list()
    
    # Generate a small batch of "Live" events (e.g., 50 new clicks)
    generate_web_logs(dim_customers, product_ids, num_events=50)
    
    # 2. Process the stream immediately
    process_web_logs()
    print("   ✅ [Real-Time] Sync Complete.")

# --- PIPELINE: BATCH LANE (Heavy Load) ---
# Goal: Process Sales, Inventory, Dimensions (e.g., Daily or every few minutes)
@with_retries(max_attempts=2) # Fewer retries for heavy jobs
def run_batch_sync():
    print(f"\n📦 [Batch] Starting Warehouse Sync at {datetime.now().strftime('%H:%M:%S')}...")
    
    # 1. Full Data Generation (Simulates nightly dump from ERP/Warehouse)
    generate_full_batch()
    
    # 2. Full ETL Processing
    process_dimensions()
    process_facts()
    
    # Run web logs too, just to be safe/catch up
    process_web_logs()
    
    print("   ✅ [Batch] Warehouse Sync Complete.")

# --- MAIN SCHEDULER ---
def start_scheduler():
    print("🤖 Intelligent Data Hub Orchestrator")
    print("   =================================")
    print("   MODE: Dual-Pipeline (Real-Time + Batch)")
    print("   RESILIENCE: Auto-Retry Active")
    print("   ---------------------------------")
    
    # 1. Schedule the Fast Lane (Web Logs) -> Every 30 Seconds
    # Satisfies "Near Real-Time" requirement
    schedule.every(30).seconds.do(run_real_time_sync)
    
    # 2. Schedule the Batch Lane (Sales/Inventory) -> Every 2 Minutes
    # In production, this would be .every().day.at("01:00")
    schedule.every(2).minutes.do(run_batch_sync)
    
    # 3. Initial Bootstrap
    print("🚀 Triggering initial Batch Load to seed the system...")
    run_batch_sync()

    print("\n⏳ Scheduler Active. Waiting for triggers... (Press Ctrl+C to stop)")
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    start_scheduler()