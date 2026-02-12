import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from src.db_connector import initialize_analytics_db
from src.ml_logic import run_market_basket_analysis

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="ShelfSmart",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- INITIALIZATION ---
# Initialize the database connection (Connecting to Person A's Parquet files via src/db_connector.py)
conn = initialize_analytics_db()

# --- SIDEBAR FILTERS ---
st.sidebar.header("🛠️ Global Control Center")

# Date range filter for global context
# In a production app, we'd pull min/max dates from fact_sales
date_range = st.sidebar.date_input(
    "Select Analysis Period",
    [datetime(2010, 1, 1), datetime(2012, 12, 31)]
)

st.sidebar.markdown("---")
st.sidebar.info(
    "**System Status:**\n"
    "Backend Ingestion: Active ✅\n"
    "Storage: Partitioned Parquet\n"
    "Compute: DuckDB + Polars"
)

# --- MAIN UI ---
st.title("🛍️ Smart Retail Supply Chain & Intelligence")
st.markdown(f"**Data Hub View:** {date_range[0]} to {date_range[1]}")

# Navigation Tabs as per Project Handbook
tab_exec, tab_ops, tab_ai = st.tabs([
    "📈 Executive Summary", 
    "🚚 Real-Time Operations", 
    "🤖 AI Insights"
])

# --- TAB 1: EXECUTIVE SUMMARY ---
with tab_exec:
    st.subheader("Commercial Performance Metrics")
    
    try:
        # Fetch high-level KPIs from Person A's fact_sales
        metrics_df = conn.execute(f"""
            SELECT 
                SUM(quantity * unit_price) as total_rev,
                COUNT(DISTINCT transaction_id) as total_orders,
                AVG(quantity * unit_price) as avg_order_val
            FROM fact_sales
            WHERE transaction_date BETWEEN '{date_range[0]}' AND '{date_range[1]}'
        """).df()
        
        m1, m2, m3 = st.columns(3)
        # Check if data exists, otherwise show placeholder
        rev = metrics_df['total_rev'][0] if not metrics_df.empty else 0
        orders = metrics_df['total_orders'][0] if not metrics_df.empty else 0
        aov = metrics_df['avg_order_val'][0] if not metrics_df.empty else 0

        m1.metric("Total Revenue", f"₹{rev:,.2f}", "+5.2%")
        m2.metric("Order Volume", f"{orders:,}", "-1.4%")
        m3.metric("Avg. Order Value", f"₹{aov:,.2f}", "+0.8%")
        
        # --- INVENTORY TURNOVER KPI ---
        # Formula: SUM(quantity) / AVG(stock_on_hand)
        # Required in: "Operations Metrics: Inventory Turnover Ratio"
        try:
            turnover_df = conn.execute("""
                SELECT 
                    SUM(s.quantity) as total_quantity,
                    AVG(i.stock_on_hand) as avg_stock
                FROM fact_sales s
                LEFT JOIN fact_inventory i ON s.product_id = i.product_id
                WHERE s.transaction_date BETWEEN ? AND ?
            """, [date_range[0], date_range[1]]).df()
            
            if not turnover_df.empty and turnover_df['avg_stock'][0] is not None and turnover_df['avg_stock'][0] > 0:
                inventory_turnover = turnover_df['total_quantity'][0] / turnover_df['avg_stock'][0]
            else:
                inventory_turnover = 0
        except:
            inventory_turnover = 0
        
        st.markdown("---")
        col_left, col_right = st.columns(2)
        with col_left:
            st.write("#### Operations Metrics: Inventory Turnover Ratio")
            st.metric("Inventory Turnover", f"{inventory_turnover:.2f}x", "SUM(qty) / AVG(stock)")
            st.caption("Higher = Better inventory efficiency")
            
        with col_right:
            st.write("#### Revenue Trend by City")
            # Note: Phase 4 - SCD Type 2 Implementation
            # When city dimension has SCD Type 2 (tracking address changes), join using:
            # JOIN dim_customers c ON s.customer_id = c.customer_id
            # AND s.transaction_date BETWEEN c.start_date AND c.end_date
            # This prevents revenue duplication from the same customer in different cities
            trend_data = conn.execute("""
                SELECT c.city, SUM(s.quantity * s.unit_price) as revenue
                FROM fact_sales s
                JOIN dim_customers c ON s.customer_id = c.customer_id
                GROUP BY 1 ORDER BY 2 DESC
            """).df()
            if not trend_data.empty:
                fig = px.bar(trend_data, x='city', y='revenue', color='city', template="plotly_white")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.caption("Awaiting City-based sales data...")

        with col_right:
            st.write("#### Top 10 High-Velocity Products")
            top_prods = conn.execute("""
                SELECT p.description, SUM(s.quantity) as volume
                FROM fact_sales s
                JOIN dim_products p ON s.product_id = p.product_id
                WHERE s.quantity > 0
                GROUP BY 1 ORDER BY 2 DESC LIMIT 10
            """).df()
            if not top_prods.empty:
                fig_prod = px.pie(top_prods, values='volume', names='description', hole=0.4)
                st.plotly_chart(fig_prod, use_container_width=True)
            else:
                st.caption("Awaiting Product sales data...")
                
    except Exception as e:
        st.warning("⚠️ Connection to Data Hub pending. Check if Person A has generated 'data_hub/fact_sales.parquet'.")

# --- TAB 2: REAL-TIME OPERATIONS ---
with tab_ops:
    st.subheader("Supply Chain & Logistics Health")
    
    # Showcase "Resilience" here (Web Logs status)
    st.warning("🔄 Live Stream: Listening for new JSON logs in `raw_data/stream/`...")
    
    o1, o2 = st.columns(2)
    with o1:
        st.write("#### Inventory Status")
        st.caption("Tracking stock_on_hand across dim_stores via fact_inventory")
        try:
            inv_data = conn.execute("""
                SELECT s.store_name, SUM(i.stock_on_hand) as stock
                FROM fact_inventory i
                JOIN dim_stores s ON i.store_id = s.store_id
                GROUP BY 1
            """).df()
            if not inv_data.empty:
                st.bar_chart(inv_data.set_index('store_name'))
            else:
                st.progress(0, text="Awaiting Inventory data...")
        except:
            st.info("Inventory metrics will populate upon the next scheduled ETL run.")

    with o2:
        st.write("#### Shipment Performance")
        st.caption("Analyzing delivery_time_days from fact_shipments")
        
        # --- DYNAMIC AVERAGE DELIVERY TIME ---
        # Previously hardcoded: "3.4 Days"
        # Now querying: SELECT AVG(delivery_time_days) FROM fact_shipments
        try:
            delivery_df = conn.execute(f"""
                SELECT AVG(delivery_time_days) as avg_delivery_time
                FROM fact_shipments
                WHERE shipment_date BETWEEN '{date_range[0]}' AND '{date_range[1]}'
            """).df()
            
            if not delivery_df.empty and delivery_df['avg_delivery_time'][0] is not None:
                avg_delivery_days = delivery_df['avg_delivery_time'][0]
                st.metric("Avg. Delivery Time", f"{avg_delivery_days:.1f} Days", "-0.2 Days")
            else:
                st.metric("Avg. Delivery Time", "No Data", "Awaiting Shipments")
        except:
            st.metric("Avg. Delivery Time", "N/A", "Query Error")

# --- TAB 3: AI INSIGHTS ---
with tab_ai:
    st.subheader("Predictive Analytics & Intelligence")
    
    ai_col1, ai_col2 = st.columns([2, 1])
    
    with ai_col1:
        st.write("#### Market Basket Analysis")
        if st.button("🚀 Run Analysis on Current Batch"):
            try:
                # Prepare data for ML logic
                ml_data = conn.execute("""
                    SELECT s.transaction_id, p.description as product_name
                    FROM fact_sales s
                    JOIN dim_products p ON s.product_id = p.product_id
                    WHERE s.quantity > 0
                """).df()
                
                if not ml_data.empty:
                    rules = run_market_basket_analysis(ml_data)
                    st.dataframe(rules, use_container_width=True)
                else:
                    st.error("Incomplete data for ML processing.")
            except Exception as e:
                st.error(f"ML Processing Error: {e}")
    
    with ai_col2:
        st.write("#### Intelligence Tools")
        # Interactive Product Recommender
        st.selectbox("Select a Product to see Associations:", ["Loading StockCodes...", "85123A", "22423", "47566"])
        
        # --- CLV CALCULATION (PHASE 2) ---
        st.write("#### Customer Lifetime Value (CLV)")
        st.caption("Phase 2 Implementation: CLV = AOV × Frequency × Lifespan")
        
        try:
            # Calculate CLV for top customers
            # Formula: Avg Order Value × Purchase Frequency × Lifespan (in years)
            clv_df = conn.execute(f"""
                SELECT 
                    c.customer_id,
                    c.customer_name,
                    COUNT(DISTINCT s.transaction_id) as purchase_frequency,
                    AVG(s.quantity * s.unit_price) as avg_order_value,
                    1.0 as lifespan_years,  -- Placeholder: can be calculated from first/last order dates
                    (COUNT(DISTINCT s.transaction_id) * AVG(s.quantity * s.unit_price) * 1.0) as clv_estimate
                FROM dim_customers c
                LEFT JOIN fact_sales s ON c.customer_id = s.customer_id
                WHERE s.transaction_date BETWEEN '{date_range[0]}' AND '{date_range[1]}'
                GROUP BY c.customer_id, c.customer_name
                ORDER BY clv_estimate DESC
                LIMIT 5
            """).df()
            
            if not clv_df.empty:
                st.dataframe(clv_df[['customer_name', 'purchase_frequency', 'avg_order_value', 'clv_estimate']], 
                           use_container_width=True)
            else:
                st.info("CLV data will populate upon the next scheduled ETL run.")
        except Exception as e:
            st.caption(f"CLV Calculation: Awaiting data... ({str(e)[:30]})")

# --- FOOTER ---
st.markdown("---")
st.caption(f"PROJECT EXECUTION HANDBOOK | PHASE 1 & 2 INTEGRATED | LAST REFRESH: {datetime.now().strftime('%H:%M:%S')}")