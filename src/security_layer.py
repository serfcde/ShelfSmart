import duckdb
import os

# Paths
HUB_DIR = "data_hub"
DB_PATH = os.path.join(HUB_DIR, "retail_vault.duckdb")

def setup_security_layer():
    print("🔐 Initializing Security & Storage Layer (DuckDB)...")
    
    # 1. Connect to (or create) a local DuckDB file
    con = duckdb.connect(DB_PATH)

    # 2. Register Parquet files as Virtual Tables
    print("📦 Registering Parquet files as tables...")
    
    con.execute(f"CREATE OR REPLACE VIEW raw_customers AS SELECT * FROM '{HUB_DIR}/dim_customers.parquet'")
    con.execute(f"CREATE OR REPLACE VIEW raw_products AS SELECT * FROM '{HUB_DIR}/dim_products.parquet'")
    con.execute(f"CREATE OR REPLACE VIEW raw_stores AS SELECT * FROM '{HUB_DIR}/dim_stores.parquet'")
    con.execute(f"CREATE OR REPLACE VIEW raw_sales AS SELECT * FROM '{HUB_DIR}/fact_sales.parquet'")
    con.execute(f"CREATE OR REPLACE VIEW raw_inventory AS SELECT * FROM '{HUB_DIR}/fact_inventory.parquet'")
    con.execute(f"CREATE OR REPLACE VIEW raw_web_events AS SELECT * FROM '{HUB_DIR}/fact_web_events.parquet'")

    # 3. Create SECURE VIEWS (Access Control)
   
    print("🛡️ Creating Secure Views for PII protection...")
    con.execute("""
        CREATE OR REPLACE VIEW secure_customers AS 
        SELECT 
            customer_id, 
            name, 
            city,
            update_timestamp,
            is_current,
            regexp_replace(email, '(^.{3})(.*)(@.*$)', '\\1****\\3') as masked_email
        FROM raw_customers
    """)

    # 4. Create ANALYTICS VIEWS (Simplifying life for Person B)
    print("📊 Creating Gold-Layer Analytics Views...")
    con.execute("""
        CREATE OR REPLACE VIEW analytics_sales_performance AS
        SELECT 
            s.transaction_id,
            s.transaction_date,
            p.description as product_name,
            p.category,
            st.store_name,
            st.city as store_city,
            s.quantity,
            s.unit_price,
            (s.quantity * s.unit_price) as total_revenue
        FROM raw_sales s
        LEFT JOIN raw_products p ON s.product_id = p.product_id
        LEFT JOIN raw_stores st ON s.store_id = st.store_id
    """)
    
    # 5. Create WEB ANALYTICS VIEW
    # Flatten web events with product details for easier querying
    con.execute("""
        CREATE OR REPLACE VIEW analytics_web_engagement AS
        SELECT 
            we.session_id,
            we.customer_id,
            we.event_type,
            we.event_date,
            we.timestamp,
            we.device_type,
            we.referrer,
            p.description as product_name,
            p.category as product_category,
            we.product_id,
            we.quantity,
            we.promo_code,
            CASE WHEN we.event_type = 'checkout_completed' THEN we.transaction_id ELSE NULL END as purchase_txn_id
        FROM raw_web_events we
        LEFT JOIN raw_products p ON we.product_id = p.product_id
    """)

    print(f"✅ Security Layer established in: {DB_PATH}")
    
    # Quick Test: Try to read the customers
    print("\n🕵️ Testing Security (Selecting from secure_customers):")
    # We explicitly select masked_email to verify the fix
    test_query = con.execute("SELECT name, masked_email, city FROM secure_customers LIMIT 3").df()
    print(test_query)
    
    con.close()

if __name__ == "__main__":
    setup_security_layer()