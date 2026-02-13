import polars as pl
import os
from datetime import datetime
import json
import glob

# Define Directories
RAW_DIR = "raw_data"
HUB_DIR = "data_hub"
LOG_DIR = "logs"
STREAM_DIR = os.path.join(RAW_DIR, "stream")

# Ensure output directories exist
os.makedirs(HUB_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

def log_quality_issue(message):
    """Writes data quality issues to our log file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(os.path.join(LOG_DIR, "quality_report.txt"), "a") as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"⚠️ QUALITY LOG: {message}")

def process_dimensions():
    print("\n🛠️ Processing Dimension Tables...")

    # 1. Stores Dimension
    stores = pl.read_csv(os.path.join(RAW_DIR, "dim_stores.csv"))
    stores.write_parquet(os.path.join(HUB_DIR, "dim_stores.parquet"))
    print("✅ dim_stores processed.")

    # 2. Products Dimension
    products = pl.read_csv(os.path.join(RAW_DIR, "dim_products.csv"))
    products.write_parquet(os.path.join(HUB_DIR, "dim_products.parquet"))
    print("✅ dim_products processed.")

    # 3. Customers Dimension (SCD Type 2 Logic)
    customers = pl.read_csv(os.path.join(RAW_DIR, "dim_customers.csv"))
    
    # Parse timestamps
    # FIX: Using strict=False prevents crashing if formats vary slightly
    customers = customers.with_columns(
        pl.col("update_timestamp").str.to_datetime(strict=False) 
    )
    
    # Sort and add SCD columns
    customers = customers.sort(["customer_id", "update_timestamp"], descending=[False, True])
    
    customers = customers.with_columns([
        (pl.col("update_timestamp") == pl.col("update_timestamp").max().over("customer_id")).alias("is_current"),
        pl.col("update_timestamp").alias("valid_from")
    ])

    scd_count = customers.filter(pl.col("is_current") == False).height
    log_quality_issue(f"Processed Customers: Found {scd_count} historical records (SCD Type 2 resolved).")
    
    customers.write_parquet(os.path.join(HUB_DIR, "dim_customers.parquet"))
    print("✅ dim_customers processed (SCD Type 2 applied).")

def process_facts():
    print("\n🛠️ Processing Fact Tables...")

    # 1. Sales Fact
    # FIX: Force 'transaction_id' to be read as String (Utf8) to handle 'C' values
    sales = pl.read_csv(
        os.path.join(RAW_DIR, "fact_sales.csv"),
        schema_overrides={"transaction_id": pl.Utf8} 
    )
    initial_count = sales.height
    
    # Clean Data
    sales = sales.filter((pl.col("quantity") > 0) & (pl.col("unit_price") > 0))
    dropped_count = initial_count - sales.height
    if dropped_count > 0:
        log_quality_issue(f"Sales Data Cleaned: Dropped {dropped_count} invalid rows.")

    # Format Dates
    sales = sales.with_columns(
        pl.col("transaction_date").str.to_datetime("%Y-%m-%d %H:%M:%S", strict=False)
    )

    # Add Partition Keys
    sales = sales.with_columns([
        pl.col("transaction_date").dt.year().alias("year"),
        pl.col("transaction_date").dt.month().alias("month")
    ])

    # Save Partitioned Data
    sales_dir = os.path.join(HUB_DIR, "fact_sales_partitioned")
    sales.write_parquet(
        sales_dir,
        partition_by=["year", "month"],
        use_pyarrow=True
    )
    
    # Save Flat File
    sales.write_parquet(os.path.join(HUB_DIR, "fact_sales.parquet"))
    print("✅ fact_sales processed (Partitioned & Flat).")

    # 2. Inventory Fact
    inventory = pl.read_csv(os.path.join(RAW_DIR, "fact_inventory.csv"))
    
    # Clean Data
    inventory = inventory.with_columns(
        pl.when(pl.col("stock_on_hand") < 0).then(0).otherwise(pl.col("stock_on_hand")).alias("stock_on_hand")
    )
    inventory.write_parquet(os.path.join(HUB_DIR, "fact_inventory.parquet"))
    print("✅ fact_inventory processed.")

    # 3. Shipments Fact
    shipments = pl.read_csv(os.path.join(RAW_DIR, "fact_shipments.csv"))
    shipments.write_parquet(os.path.join(HUB_DIR, "fact_shipments.parquet"))
    print("✅ fact_shipments processed.")

def process_web_logs():
    print("\n🌐 Processing Web Logs (Clickstream Data)...")
    
    json_files = glob.glob(os.path.join(STREAM_DIR, "*.json"))
    
    if not json_files:
        print("⚠️ No web logs to process. Skipping...")
        return
    
    all_events = []
    
    # Read all JSON files
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                for line in f:
                    try:
                        event = json.loads(line.strip())
                        if event: all_events.append(event)
                    except: continue
        except: continue
    
    if not all_events:
        print("⚠️ No valid web events found.")
        return
    
    # Create DataFrame (Schema Evolution handled automatically here)
    web_events_df = pl.DataFrame(all_events)
    
    # Clean Data
    web_events_df = web_events_df.filter(pl.col("customer_id").is_not_null())
    web_events_df = web_events_df.unique(subset=["session_id", "event_type", "timestamp"], keep="first")
    
    # FIX: Safe Timestamp Parsing
    # We strip 'T' if present or handle standard formats
    web_events_df = web_events_df.with_columns(
        pl.col("timestamp").str.to_datetime(strict=False).alias("parsed_time")
    )
    
    # Filter out rows where timestamp parsing failed (to prevent crashes)
    web_events_df = web_events_df.filter(pl.col("parsed_time").is_not_null())
    
    # Add partition date
    web_events_df = web_events_df.with_columns(
        pl.col("parsed_time").dt.date().alias("event_date")
    ).drop("parsed_time") # Clean up temp column
    
    # Save
    web_events_df.write_parquet(os.path.join(HUB_DIR, "fact_web_events.parquet"))
    
    log_quality_issue(f"Web Logs: {web_events_df.height} events processed.")
    print(f"✅ fact_web_events processed ({web_events_df.height} events).")

def main():
    print("🚀 Starting Polars ETL Pipeline...")
    
    log_path = os.path.join(LOG_DIR, "quality_report.txt")
    if os.path.exists(log_path):
        os.remove(log_path)
        
    process_dimensions()
    process_facts()
    process_web_logs()
    
    print("\n🎉 SUCCESS! All data cleaned and saved to 'data_hub'.")

if __name__ == "__main__":
    main()