import polars as pl
from faker import Faker
import random
from datetime import datetime, timedelta
import os

# Initialize Faker with an Indian locale as per the problem statement
fake = Faker('en_IN')

# Define paths
RAW_DATA_DIR = "raw_data"
INPUT_FILE = os.path.join(RAW_DATA_DIR, "Online Retail.csv")

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
    
    # Generate names, emails, and base dates
    dim_customers = dim_customers.with_columns([
        pl.Series("name", [fake.name() for _ in range(dim_customers.height)]),
        pl.Series("email", [fake.email() for _ in range(dim_customers.height)]),
        pl.Series("update_timestamp", [datetime.now() - timedelta(days=random.randint(50, 200)) for _ in range(dim_customers.height)])
    ])
    dim_customers = dim_customers.rename({"CustomerID": "customer_id", "Country": "city"})

    # INJECT SCD TYPE 2 TRAP: Pick 5% of customers and simulate them moving to an Indian city
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
    fact_sales = df.select(["InvoiceNo", "CustomerID", "StockCode", "Quantity", "UnitPrice", "InvoiceDate"])
    
    # Randomly assign each transaction to a store
    fact_sales = fact_sales.with_columns([
        pl.Series("store_id", [random.choice(store_ids) for _ in range(fact_sales.height)])
    ])
    
    fact_sales = fact_sales.rename({
        "InvoiceNo": "transaction_id",
        "CustomerID": "customer_id",
        "StockCode": "product_id",
        "Quantity": "quantity",
        "UnitPrice": "unit_price",
        "InvoiceDate": "transaction_date"
    })
    
    # Note: The real dataset already has negative quantities (returns/cancellations) 
    # and 0 unit prices. This acts as our perfect "Quality Trap" for Step 3!
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

    print("✅ SUCCESS! All 6 Star Schema CSVs have been generated in the 'raw_data' folder.")

if __name__ == "__main__":
    main()