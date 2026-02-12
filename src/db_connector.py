import duckdb
import os

def initialize_analytics_db():
    """
    Creates a high-performance DuckDB connection that maps Parquet files 
    from the 'data_hub' folder into SQL views.
    
    This allows Person B (Analyst) to query the backend data using standard SQL
    without needing a dedicated database server.
    """
    conn = duckdb.connect(database=':memory:')
    
    data_hub_path = "data_hub"
    

    schema_map = {
        'dim_customers': 'dim_customers.parquet',
        'dim_products': 'dim_products.parquet',
        'dim_stores': 'dim_stores.parquet',
        'fact_sales': 'fact_sales.parquet',
        'fact_inventory': 'fact_inventory.parquet',
        'fact_shipments': 'fact_shipments.parquet',
        'fact_web_events': 'fact_web_events.parquet'
    }
    
    # Register each Parquet file as a virtual SQL table (View)
    for table_name, file_name in schema_map.items():
        file_path = os.path.join(data_hub_path, file_name)
        
        if os.path.exists(file_path):
            
            try:
                conn.execute(f"CREATE OR REPLACE VIEW {table_name} AS SELECT * FROM read_parquet('{file_path}')")
            except Exception as e:
                print(f"Error registering {table_name}: {e}")
        else:
            # SAFETY FEATURE
            print(f"Warning: {file_path} not found. Creating empty placeholder for {table_name}.")
            
            # We create a simple table structure so SELECT * doesn't fail
            conn.execute(f"CREATE TABLE IF NOT EXISTS {table_name} (id INTEGER)")
            
    return conn

if __name__ == "__main__":
    try:
        db = initialize_analytics_db()
        print("✅ Success: DuckDB initialized and Parquet views registered.")
        
        # Check if we can see the tables
        tables = db.execute("SHOW TABLES").df()
        print("Available Tables:")
        print(tables)
    except Exception as e:
        print(f"❌ Initialization Failed: {e}")