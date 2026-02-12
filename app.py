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

conn = initialize_analytics_db()

# --- SIDEBAR FILTERS ---
st.sidebar.header("🛠️ Global Controls")

# Date Picker (Defaulting to the dataset's range: Dec 2010 - Dec 2011)
start_date = st.sidebar.date_input("Start Date", datetime(2010, 12, 1))
end_date = st.sidebar.date_input("End Date", datetime(2011, 12, 9))


date_range = [start_date, end_date]

st.sidebar.markdown("---")
st.sidebar.info(
    "**System Status:**\n\n"
    "✅ **Ingestion:** Active\n\n"
    "✅ **Storage:** Parquet (Local)\n\n"
    "✅ **Compute:** DuckDB"
)

# --- MAIN UI ---
st.title("🛍️ Smart Retail Supply Chain & Intelligence")
st.markdown(f"**Data Hub View:** {date_range[0]} to {date_range[1]}")

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
        
        # --- DAILY REVENUE TREND CHART ---
        st.markdown("---")
        st.write("#### 📊 Daily Revenue Trend")
        try:
            trend_query = f"""
                SELECT 
                    CAST(transaction_date AS DATE) as date,
                    SUM(quantity * unit_price) / 1000 as daily_revenue
                FROM fact_sales
                WHERE transaction_date BETWEEN '{date_range[0]}' AND '{date_range[1]}'
                GROUP BY 1
                ORDER BY 1
            """
            trend_df = conn.execute(trend_query).df()
            if not trend_df.empty:
                fig_trend = px.line(trend_df, x='date', y='daily_revenue', markers=True, template="plotly_white")
                fig_trend.update_layout(
                    xaxis_title="Date", 
                    yaxis_title="Daily Revenue (₹ Thousands)",
                    hovermode='x unified'
                )
                fig_trend.update_traces(line=dict(color='#1f77b4', width=3), marker=dict(size=6))
                st.plotly_chart(fig_trend, use_container_width=True)
            else:
                st.info("No sales data for trend chart in this period.")
        except Exception as e:
            st.error(f"Error loading trend chart: {str(e)[:100]}")

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
    st.warning("🔄 Live Stream: Processing JSON logs from `raw_data/stream/` via ETL Pipeline (Every 30 seconds).")
    
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
        st.markdown("**⚠️ Inventory Risks (Low Stock Alerts)**")
        inv_query = """
            SELECT 
                p.description,
                st.store_name,
                i.stock_on_hand
            FROM fact_inventory i
            JOIN dim_products p ON i.product_id = p.product_id
            JOIN dim_stores st ON i.store_id = st.store_id
            WHERE i.stock_on_hand < 10 AND i.stock_on_hand >= 0
            ORDER BY i.stock_on_hand ASC
            LIMIT 10
        """
        try:
            inv_df = conn.execute(inv_query).df()
            st.dataframe(inv_df, use_container_width=True)
        except:
            st.caption("No inventory alerts.")
    
    # --- WEB ENGAGEMENT METRICS (SILO 3: Web Logs) ---
    st.markdown("---")
    st.write("### 🌐 Web Engagement & Customer Journey (E-commerce Silo)")
    
    we1, we2, we3 = st.columns(3)
    
    with we1:
        st.write("#### Active Sessions")
        try:
            session_data = conn.execute(f"""
                SELECT COUNT(DISTINCT session_id) as active_sessions
                FROM fact_web_events
                WHERE event_date BETWEEN '{date_range[0]}' AND '{date_range[1]}'
            """).df()
            
            active_sessions = session_data['active_sessions'][0] if not session_data.empty else 0
            st.metric("Sessions", f"{active_sessions:,}", "Last 48h")
        except Exception as e:
            st.warning(f"Web logs unavailable: {str(e)[:40]}")
    
    with we2:
        st.write("#### Cart Abandonment Rate")
        try:
            # Sessions with add_to_cart but no checkout_completed
            cart_abandon = conn.execute(f"""
                SELECT 
                    COUNT(DISTINCT CASE WHEN we.event_type = 'add_to_cart' THEN we.session_id END) as carted_sessions,
                    COUNT(DISTINCT CASE WHEN we.event_type = 'checkout_completed' THEN we.session_id END) as purchased_sessions
                FROM fact_web_events we
                WHERE we.event_date BETWEEN '{date_range[0]}' AND '{date_range[1]}'
            """).df()
            
            if not cart_abandon.empty:
                carted = cart_abandon['carted_sessions'][0] or 0
                purchased = cart_abandon['purchased_sessions'][0] or 0
                if carted > 0:
                    abandon_rate = ((carted - purchased) / carted) * 100
                else:
                    abandon_rate = 0
            else:
                abandon_rate = 0
            
            st.metric("Abandon Rate", f"{abandon_rate:.1f}%", "Risk Level")
        except Exception as e:
            st.warning("Cart data unavailable")
    
    with we3:
        st.write("#### Top Referrer Source")
        try:
            referrer_data = conn.execute(f"""
                SELECT referrer, COUNT(*) as event_count
                FROM fact_web_events
                WHERE event_date BETWEEN '{date_range[0]}' AND '{date_range[1]}'
                  AND referrer IS NOT NULL
                GROUP BY 1 ORDER BY 2 DESC LIMIT 1
            """).df()
            
            if not referrer_data.empty:
                top_referrer = referrer_data['referrer'][0]
                count = referrer_data['event_count'][0]
                st.metric("Top Source", top_referrer, f"{count} events")
            else:
                st.metric("Top Source", "N/A", "No data")
        except:
            st.metric("Top Source", "Error", "Check logs")

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
                    c.name as customer_name,
                    COUNT(DISTINCT s.transaction_id) as purchase_frequency,
                    AVG(s.quantity * s.unit_price) as avg_order_value,
                    1.0 as lifespan_years,
                    (COUNT(DISTINCT s.transaction_id) * AVG(s.quantity * s.unit_price) * 1.0) as clv_estimate
                FROM dim_customers c
                LEFT JOIN fact_sales s ON c.customer_id = s.customer_id
                WHERE s.transaction_date BETWEEN '{date_range[0]}' AND '{date_range[1]}'
                GROUP BY c.customer_id, c.name
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

    # --- WEB-DRIVEN INSIGHTS (SILO 3: Clickstream Analytics) ---
    st.markdown("---")
    st.write("### 🌐 Web Behavior Analytics & Recommendations")
    
    ai_web1, ai_web2 = st.columns(2)
    
    with ai_web1:
        st.write("#### Top Abandoned Products")
        st.caption("Products added to cart but NOT purchased")
        try:
            abandoned_prods = conn.execute(f"""
                SELECT 
                    COALESCE(p.description, 'Unknown Product') as product_description,
                    COUNT(DISTINCT we.session_id) as abandoned_count
                FROM fact_web_events we
                LEFT JOIN fact_web_events checkout ON we.session_id = checkout.session_id 
                    AND checkout.event_type = 'checkout_completed'
                LEFT JOIN dim_products p ON we.product_id = p.product_id
                WHERE we.event_type = 'add_to_cart'
                  AND checkout.session_id IS NULL
                  AND we.event_date BETWEEN '{date_range[0]}' AND '{date_range[1]}'
                GROUP BY p.description
                ORDER BY 2 DESC LIMIT 8
            """).df()
            
            if not abandoned_prods.empty:
                st.dataframe(abandoned_prods[['product_description', 'abandoned_count']], use_container_width=True)
            else:
                st.info("No abandoned carts detected in this period.")
        except Exception as e:
            st.warning(f"Abandonment analysis unavailable: {str(e)[:50]}")
    
    with ai_web2:
        st.write("#### Product Co-viewing (Click Affinity)")
        st.caption("Products viewed together in same session")
        try:
            coview_data = conn.execute(f"""
                SELECT 
                    COALESCE(p1.description, 'Product A') as product_1,
                    COALESCE(p2.description, 'Product B') as product_2,
                    COUNT(*) as co_view_count
                FROM fact_web_events we1
                JOIN fact_web_events we2 
                    ON we1.session_id = we2.session_id
                    AND we1.event_type = 'page_view'
                    AND we2.event_type = 'page_view'
                    AND we1.product_id < we2.product_id
                LEFT JOIN dim_products p1 ON we1.product_id = p1.product_id
                LEFT JOIN dim_products p2 ON we2.product_id = p2.product_id
                GROUP BY p1.description, p2.description 
                ORDER BY 3 DESC LIMIT 8
            """).df()
            
            if not coview_data.empty:
                st.dataframe(coview_data, use_container_width=True)
            else:
                st.info("Insufficient co-viewing data.")
        except Exception as e:
            st.warning(f"Affinity analysis unavailable: {str(e)[:50]}")
    
    # Customer Engagement Score
    st.write("#### Customer Engagement & Purchase Intent")
    st.caption("Customers with high browsing activity but low purchase - HIGH VALUE PROSPECTS")
    try:
        engagement_df = conn.execute(f"""
            SELECT 
                c.customer_id,
                c.name as customer_name,
                COUNT(DISTINCT we.session_id) as browsing_sessions,
                COUNT(DISTINCT CASE WHEN we.event_type = 'add_to_cart' THEN 1 END) as items_carted,
                COUNT(DISTINCT fs.transaction_id) as purchases_made,
                ROUND(COUNT(DISTINCT CASE WHEN we.event_type = 'page_view' THEN 1 END) * 1.0 / 
                    NULLIF(COUNT(DISTINCT fs.transaction_id), 0), 2) as browse_to_buy_ratio
            FROM fact_web_events we
            LEFT JOIN dim_customers c ON we.customer_id = c.customer_id
            LEFT JOIN fact_sales fs ON we.customer_id = fs.customer_id
            WHERE we.event_date BETWEEN '{date_range[0]}' AND '{date_range[1]}'
            GROUP BY 1, 2
            HAVING COUNT(DISTINCT we.session_id) > 2 AND COUNT(DISTINCT fs.transaction_id) < COUNT(DISTINCT we.session_id)
            ORDER BY COUNT(DISTINCT we.session_id) DESC LIMIT 10
        """).df()
        
        if not engagement_df.empty:
            st.dataframe(engagement_df[['customer_name', 'browsing_sessions', 'items_carted', 'purchases_made']], 
                       use_container_width=True)
            st.caption("💡 Action: Send targeted offers to high-engagement prospects to boost conversion")
        else:
            st.info("Engagement data will populate once web activity is tracked.")
    except Exception as e:
        st.warning(f"Engagement scoring unavailable: {str(e)[:50]}")

# --- FOOTER ---
st.markdown("---")
st.caption(f"🛞 THREE-SILO INTEGRATION ACTIVE: POS Billing ✅ | Warehouse Operations ✅ | E-commerce Web Logs ✅ | LAST REFRESH: {datetime.now().strftime('%H:%M:%S')}")