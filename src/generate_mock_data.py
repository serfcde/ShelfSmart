import polars as pl
from faker import Faker
import random
from datetime import datetime, timedelta
import os
import json

# Initialize Faker with an Indian locale as per the problem statement
fake = Faker('en_IN')

# Define paths
RAW_DATA_DIR = "raw_data"
INPUT_FILE = os.path.join(RAW_DATA_DIR, "Online Retail.csv")
STREAM_DIR = os.path.join(RAW_DATA_DIR, "stream")

def generate_web_logs(dim_customers, product_ids, num_events=500):
    """
    Generate synthetic web logs (clickstream data) as JSON.
    This represents the Web/E-commerce Silo in the problem statement.
    
    Schema Evolution Test: Some events have 'promo_code', others don't.
    """
    print("🌐 Generating Web Logs (E-commerce Clickstream)...")
    
    os.makedirs(STREAM_DIR, exist_ok=True)
    
    customer_ids = dim_customers["customer_id"].to_list()
    event_types = ["page_view", "search", "add_to_cart", "remove_from_cart", "checkout_start", "checkout_completed"]
    devices = ["mobile", "desktop", "tablet"]
    referrers = ["google_search", "facebook_ad", "direct", "newsletter", "instagram"]
    
    web_events = []
    session_id_counter = 1000
    
    for _ in range(num_events):
        # Create a session with 1-8 events (customer journey)
        session_events = random.randint(1, 8)
        session_id = f"sess_{session_id_counter}"
        session_id_counter += 1
        
        customer_id = random.choice(customer_ids)
        base_time = datetime.now() - timedelta(hours=random.randint(0, 48))
        
        for event_seq in range(session_events):
            event_time = base_time + timedelta(minutes=random.randint(event_seq * 2, event_seq * 2 + 5))
            event_type = random.choice(event_types)
            
            event = {
                "session_id": session_id,
                "customer_id": int(customer_id),
                "event_type": event_type,
                "timestamp": event_time.isoformat(),
                "device_type": random.choice(devices),
                "referrer": random.choice(referrers)
            }
            
            # Add product context for browsing/cart events
            if event_type in ["page_view", "add_to_cart", "remove_from_cart", "search"]:
                event["product_id"] = random.choice(product_ids)
                event["duration_seconds"] = random.randint(10, 300) if event_type == "page_view" else None
                
            # SCHEMA EVOLUTION TRAP: Randomly add promo_code (not all events have it)
            if random.random() < 0.15:  # 15% of events
                event["promo_code"] = random.choice(["SAVE10", "WELCOME20", "FLASH35", None])
            
            # Add quantity only for add_to_cart and remove_from_cart
            if event_type in ["add_to_cart", "remove_from_cart"]:
                event["quantity"] = random.randint(1, 5)
            
            # Add checkout details only for checkout events
            if event_type == "checkout_completed":
                event["transaction_id"] = f"TXN_{random.randint(100000, 999999)}"
                event["total_value"] = round(random.uniform(500, 5000), 2)
            
            web_events.append(event)
    
    # Write web logs to JSON file (simulating real-time streaming arrival)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(STREAM_DIR, f"web_events_{timestamp}.json")
    
    with open(log_file, 'w') as f:
        for event in web_events:
            f.write(json.dumps(event) + "\n")  # JSONL format (one JSON per line)
    
    print(f"✅ Web logs generated: {len(web_events)} events in {log_file}")

def main():
    print("🚀 Starting Data Generation & Mapping Process...")
    
    # 1. Check if the input file exists
    if not os.path.exists(INPUT_FILE):
        print(f"❌ ERROR: Could not find '{INPUT_FILE}'.")
        print("Please make sure you extracted the zip and placed the CSV exactly in the 'raw_data' folder.")
        return

    # 2. Load the Real Dataset
    print("⏳ Loading real dataset using Polars...")
    # The real dataset often has encoding issues, ignore_errors helps bypass bad characters
    df = pl.read_csv(INPUT_FILE, ignore_errors=True, truncate_ragged_lines=True)
    
    # Clean up baseline data (Drop rows without CustomerID so we can build a proper Star Schema)
    df = df.drop_nulls(subset=["CustomerID"])
    
    # Clean column names to match our schema expectations and cast CustomerID to Integer
    df = df.with_columns(pl.col("CustomerID").cast(pl.Int64))

    # ==========================================
    # DIMENSION 1: STORES (Generate completely)
    # ==========================================
    print("📦 Generating Stores Dimension...")
    num_stores = 55 # 50+ stores requested in problem statement
    stores_data = {
        "store_id": [f"ST_{i:03d}" for i in range(1, num_stores + 1)],
        "store_name": [f"Retail Hub {fake.city()}" for _ in range(num_stores)],
        "city": [fake.city() for _ in range(num_stores)]
    }
    dim_stores = pl.DataFrame(stores_data)
    dim_stores.write_csv(os.path.join(RAW_DATA_DIR, "dim_stores.csv"))
    store_ids = dim_stores["store_id"].to_list()

    # ==========================================
    # DIMENSION 2: PRODUCTS (Extract + Generate)
    # ==========================================
    print("🛍️ Generating Products Dimension...")
    dim_products = df.select(["StockCode", "Description", "UnitPrice"]).unique(subset=["StockCode"])
    categories = ["Electronics", "Apparel", "Home & Garden", "Toys", "Groceries", "Logistics"]
    
    dim_products = dim_products.with_columns([
        pl.Series("category", [random.choice(categories) for _ in range(dim_products.height)]),
        pl.Series("supplier_id", [f"SUP_{random.randint(100, 999)}" for _ in range(dim_products.height)])
    ])
    dim_products = dim_products.rename({
        "StockCode": "product_id", 
        "Description": "description", 
        "UnitPrice": "base_price"
    })
    dim_products.write_csv(os.path.join(RAW_DATA_DIR, "dim_products.csv"))
    product_ids = dim_products["product_id"].to_list()

    # ==========================================
    # DIMENSION 3: CUSTOMERS (Extract + Generate)
    # ==========================================
    print("👥 Generating Customers Dimension (with SCD Type 2 Traps)...")
    dim_customers = df.select(["CustomerID", "Country"]).unique(subset=["CustomerID"])
    
    # ==========================================
    # DIMENSION 3: CUSTOMERS (Extract + Generate)
    # ==========================================
    print("👥 Generating Customers Dimension (with SCD Type 2 Traps)...")
    
    # FIX: Select BOTH CustomerID and Country if you want to rename Country later,
    # OR just select CustomerID and add a 'city' column manually.
    dim_customers = df.select(["CustomerID"]).unique(subset=["CustomerID"])
    
    # Generate names, emails, base dates, AND CITIES
    dim_customers = dim_customers.with_columns([
        pl.Series("name", [fake.name() for _ in range(dim_customers.height)]),
        pl.Series("email", [fake.email() for _ in range(dim_customers.height)]),
        # We generate a fake Indian city for every customer here
        pl.Series("city", [fake.city() for _ in range(dim_customers.height)]), 
        pl.Series("update_timestamp", [datetime.now() - timedelta(days=random.randint(50, 200)) for _ in range(dim_customers.height)])
    ])

    # FIX: Removed "Country": "city" from the rename mapping since we created 'city' above
    dim_customers = dim_customers.rename({"CustomerID": "customer_id"})

    # INJECT SCD TYPE 2 TRAP: Pick 5% of customers and simulate them moving
    scd_trap = dim_customers.sample(fraction=0.05)
    scd_trap = scd_trap.with_columns([
        pl.Series("city", [fake.city() for _ in range(scd_trap.height)]),
        pl.Series("update_timestamp", [datetime.now() - timedelta(days=random.randint(1, 10)) for _ in range(scd_trap.height)])
    ])
    
    # Combine original and updated records to create duplicates for the ETL to handle
    dim_customers = pl.concat([dim_customers, scd_trap])
    dim_customers.write_csv(os.path.join(RAW_DATA_DIR, "dim_customers.csv"))

    
    # ==========================================
    # FACT 1: SALES (Extract + Link)
    # ==========================================
    print("🛒 Generating Sales Fact Table...")
    # Remove InvoiceDate from the select
    fact_sales = df.select(["InvoiceNo", "CustomerID", "StockCode", "Quantity", "UnitPrice"])
    
    # Randomly assign stores AND generate recent dates
    fact_sales = fact_sales.with_columns([
        pl.Series("store_id", [random.choice(store_ids) for _ in range(fact_sales.height)]),
        # FIX: Generate transaction dates for the last 1 year relative to now
        pl.Series("transaction_date", [fake.date_time_between(start_date="-1y", end_date="now") for _ in range(fact_sales.height)])
    ])
    
    fact_sales = fact_sales.rename({
        "InvoiceNo": "transaction_id",
        "CustomerID": "customer_id",
        "StockCode": "product_id",
        "Quantity": "quantity",
        "UnitPrice": "unit_price"
        # Removed InvoiceDate rename since we generated it manually above
    })
    fact_sales.write_csv(os.path.join(RAW_DATA_DIR, "fact_sales.csv"))

    # ==========================================
    # FACT 2: INVENTORY (Generate + Link)
    # ==========================================
    print("📦 Generating Inventory Fact Table...")
    # Taking a sample of products so the dataset doesn't take hours to generate
    sample_products = random.sample(product_ids, min(300, len(product_ids))) 
    inv_data = []
    
    for s_id in store_ids:
        for p_id in sample_products:
            inv_data.append({
                "store_id": s_id,
                "product_id": p_id,
                "stock_on_hand": random.randint(-50, 500), # Injecting negative stock to test ETL cleaning!
                "last_restock_date": fake.date_time_between(start_date="-30d", end_date="now")
            })
            
    fact_inventory = pl.DataFrame(inv_data)
    fact_inventory.write_csv(os.path.join(RAW_DATA_DIR, "fact_inventory.csv"))

    # ==========================================
    # FACT 3: SHIPMENTS (Generate + Link)
    # ==========================================
    print("🚚 Generating Shipments Fact Table...")
    unique_transactions = fact_sales.select("transaction_id").unique()
    statuses = ["Processing", "Shipped", "Delivered", "Returned"]
    
    shipment_data = {
        "shipment_id": [f"SHP_{i:07d}" for i in range(1, unique_transactions.height + 1)],
        "transaction_id": unique_transactions["transaction_id"].to_list(),
        "status": [random.choice(statuses) for _ in range(unique_transactions.height)],
        "delivery_time_days": [random.randint(1, 14) for _ in range(unique_transactions.height)],
        "shipment_date": [fake.date_time_between(start_date="-1y", end_date="now") for _ in range(unique_transactions.height)]
    }
    
    fact_shipments = pl.DataFrame(shipment_data)
    fact_shipments.write_csv(os.path.join(RAW_DATA_DIR, "fact_shipments.csv"))

    # ==========================================
    # SILO 3: WEB LOGS (Generate Mock JSON)
    # ==========================================
    # Convert back to original name for the web log generation (customer_id is the key)
    generate_web_logs(dim_customers, product_ids, num_events=500)

    print("✅ SUCCESS! All 6 Star Schema CSVs + Web Logs have been generated.")
    print("   - Star Schema Tables: raw_data/*.csv")
    print("   - Web Logs (JSON): raw_data/stream/*.json")

if __name__ == "__main__":
    main()