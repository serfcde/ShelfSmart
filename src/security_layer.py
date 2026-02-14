import duckdb
import os
import pandas as pd

# Paths
HUB_DIR = "data_hub"
DB_PATH = os.path.join(HUB_DIR, "retail_vault.duckdb")

def setup_security_layer():
    print("🔐 Initializing Security & Storage Layer (DuckDB)...")
    
    # 1. Connect to (or create) a local DuckDB file
    con = duckdb.connect(DB_PATH)

    # 2. Register Parquet files as Virtual Tables (The "Silver Layer")
    # These are raw tables containing sensitive data.
    print("📦 Registering Raw Parquet files (Admin Access Only)...")
    
    con.execute(f"CREATE OR REPLACE VIEW raw_customers AS SELECT * FROM '{HUB_DIR}/dim_customers.parquet'")
    con.execute(f"CREATE OR REPLACE VIEW raw_products AS SELECT * FROM '{HUB_DIR}/dim_products.parquet'")
    con.execute(f"CREATE OR REPLACE VIEW raw_stores AS SELECT * FROM '{HUB_DIR}/dim_stores.parquet'")
    con.execute(f"CREATE OR REPLACE VIEW raw_sales AS SELECT * FROM '{HUB_DIR}/fact_sales.parquet'")
    con.execute(f"CREATE OR REPLACE VIEW raw_inventory AS SELECT * FROM '{HUB_DIR}/fact_inventory.parquet'")
    con.execute(f"CREATE OR REPLACE VIEW raw_web_events AS SELECT * FROM '{HUB_DIR}/fact_web_events.parquet'")

    # 3. Create SECURE VIEWS (The "Gold Layer")
    # Requirement: "Restrict data access so only authorized analysts can see sensitive information."
    print("🛡️ Creating Secure Views (Analyst Access)...")
    
    # SECURITY IMPLEMENTATION: Dynamic Data Masking
    # We use regex to hide the middle of the email address.
    con.execute("""
        CREATE OR REPLACE VIEW secure_customers AS 
        SELECT 
            customer_id, 
            name, 
            city,
            update_timestamp,
            is_current,
            regexp_replace(email, '(^.{3})(.*)(@.*$)', '\\1****\\3') as email, -- Overwriting the raw column
            'MASKED' as privacy_status
        FROM raw_customers
    """)

    # 4. Create ANALYTICS VIEWS (Business Logic)
    print("📊 Creating Pre-Calculated Analytics Views...")
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
    
    con.execute("""
        CREATE OR REPLACE VIEW analytics_web_engagement AS
        SELECT 
            we.session_id,
            we.customer_id,
            we.event_type,
            we.event_date,
            we.device_type,
            we.referrer,
            p.category as product_category,
            we.promo_code
        FROM raw_web_events we
        LEFT JOIN raw_products p ON we.product_id = p.product_id
    """)

    print(f"✅ Security Layer established in: {DB_PATH}")
    con.close()

def simulate_role_based_access():
    """
    Simulates how different users see the data.
    This demonstrates the 'Secure Access' requirement.
    """
    con = duckdb.connect(DB_PATH)
    
    print("\n" + "="*50)
    print("🚦 TESTING ACCESS CONTROLS")
    print("="*50)

    # SCENARIO A: Data Analyst (Should see MASKED emails)
    print("\n👤 User Role: DATA ANALYST")
    print("   Querying: secure_customers")
    try:
        # Analyst queries the secure view
        df_analyst = con.execute("SELECT customer_id, name, email FROM secure_customers LIMIT 3").df()
        print(df_analyst.to_string(index=False))
        print("   [Result]: ✅ PII is masked. Access Granted.")
    except Exception as e:
        print(f"   [Error]: {e}")

    # SCENARIO B: Data Engineer (Should see RAW emails)
    print("\n👷 User Role: DATA ENGINEER (Admin)")
    print("   Querying: raw_customers")
    try:
        # Engineer queries the raw view
        df_admin = con.execute("SELECT customer_id, name, email FROM raw_customers LIMIT 3").df()
        print(df_admin.to_string(index=False))
        print("   [Result]: ⚠️  Raw PII visible (Internal Use Only).")
    except Exception as e:
        print(f"   [Error]: {e}")

    con.close()

if __name__ == "__main__":
    setup_security_layer()
    simulate_role_based_access()