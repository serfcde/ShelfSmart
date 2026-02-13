import schedule
import time
import sys
import os
from datetime import datetime

# Add the 'src' directory to the python path so we can import our modules
sys.path.append(os.path.join(os.getcwd(), "src"))

# Import your actual modules
try:
    from generate_mock_data import main as generate_data
    from etl_pipeline import main as run_etl
except ImportError as e:
    print(f"❌ Error importing modules: {e}")
    print("Make sure you are running this script from the project root folder (Intelligent_Retail_Data_Hub).")
    sys.exit(1)

def run_full_pipeline():
    print(f"\n⏰ [Scheduler] Triggering Pipeline Job at {datetime.now().strftime('%H:%M:%S')}...")
    
    # Step 1: Simulate new data arriving (Data Gen)
    print("   --- Step 1: Ingesting Raw Data ---")
    generate_data()
    
    # Step 2: Process and Clean the data (ETL)
    print("   --- Step 2: Running ETL & Cleaning ---")
    run_etl()
    
    print(f"✅ [Scheduler] Job Complete. Waiting for next schedule...\n")

def start_scheduler():
    print("🤖 Automation Scheduler Started.")
    print("   The pipeline will run immediately, and then every 30 seconds.")
    print("   (Press Ctrl+C to stop)")
    
    # Run once immediately so we don't have to wait
    run_full_pipeline()

    # Schedule the job
    # In a real job, this might be .every().day.at("01:00")
    # For this demo/project, we use 30 seconds so you can see it working.
    schedule.every(30).seconds.do(run_full_pipeline)

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    start_scheduler()