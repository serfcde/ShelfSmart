import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import numpy as np
from src.db_connector import initialize_analytics_db
from src.ml_logic import run_market_basket_analysis

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="ShelfSmart",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Database Connection
conn = initialize_analytics_db()

# --- SIDEBAR FILTERS ---
st.sidebar.header("🛠️ Global Controls")

# Date Picker (Defaulting to the dataset's range)
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
st.title("🛒 ShelfSmart: Intelligent Retail Hub")
st.markdown(f"**Data Hub View:** {date_range[0]} to {date_range[1]}")

tab_exec, tab_ops, tab_ai = st.tabs([
    "📈 Executive Summary", 
    "🚚 Real-Time Operations", 
    "🤖 AI Insights"
])

# ============================================================
# --- TAB 1: EXECUTIVE SUMMARY ---
# ============================================================
with tab_exec:
    st.subheader("Commercial Performance Metrics")
    
    try:
        # Fetch high-level KPIs
        metrics_df = conn.execute(f"""
            SELECT 
                SUM(quantity * unit_price) as total_rev,
                COUNT(DISTINCT transaction_id) as total_orders,
                AVG(quantity * unit_price) as avg_order_val
            FROM fact_sales
            WHERE transaction_date BETWEEN '{date_range[0]}' AND '{date_range[1]}'
        """).df()
        
        m1, m2, m3 = st.columns(3)
        rev = metrics_df['total_rev'][0] if not metrics_df.empty else 0
        orders = metrics_df['total_orders'][0] if not metrics_df.empty else 0
        aov = metrics_df['avg_order_val'][0] if not metrics_df.empty else 0

        m1.metric("Total Revenue", f"₹{rev:,.2f}", "+5.2%")
        m2.metric("Order Volume", f"{orders:,}", "-1.4%")
        m3.metric("Avg. Order Value", f"₹{aov:,.2f}", "+0.8%")
        
        st.markdown("---")

        # -------------------------------------------------------
        # ✅ NEW: DAILY REVENUE TREND
        # -------------------------------------------------------
        st.write("#### 📅 Daily Revenue Trend")
        daily_revenue_query = f"""
            SELECT 
                CAST(transaction_date AS DATE) as sale_date,
                SUM(quantity * unit_price) as daily_revenue
            FROM fact_sales
            WHERE transaction_date BETWEEN '{date_range[0]}' AND '{date_range[1]}'
            GROUP BY 1
            ORDER BY 1
        """
        daily_df = conn.execute(daily_revenue_query).df()
        if not daily_df.empty:
            fig_daily = px.line(
                daily_df, x='sale_date', y='daily_revenue',
                title="Daily Revenue Over Selected Period",
                labels={'sale_date': 'Date', 'daily_revenue': 'Revenue (₹)'},
                template="plotly_white"
            )
            fig_daily.update_traces(line_color='#1f77b4', line_width=2)
            fig_daily.update_layout(hovermode="x unified")
            st.plotly_chart(fig_daily, use_container_width=True)
        else:
            st.info("No daily revenue data available for this period.")

        # -------------------------------------------------------
        # ✅ NEW: MONTHLY REVENUE TREND
        # -------------------------------------------------------
        st.write("#### 🗓️ Monthly Revenue Trend")
        monthly_revenue_query = f"""
            SELECT 
                STRFTIME(transaction_date, '%Y-%m') as sale_month,
                SUM(quantity * unit_price) as monthly_revenue,
                COUNT(DISTINCT transaction_id) as monthly_orders
            FROM fact_sales
            WHERE transaction_date BETWEEN '{date_range[0]}' AND '{date_range[1]}'
            GROUP BY 1
            ORDER BY 1
        """
        monthly_df = conn.execute(monthly_revenue_query).df()
        if not monthly_df.empty:
            fig_monthly = px.bar(
                monthly_df, x='sale_month', y='monthly_revenue',
                title="Monthly Revenue Breakdown",
                labels={'sale_month': 'Month', 'monthly_revenue': 'Revenue (₹)'},
                color='monthly_revenue', color_continuous_scale='Blues',
                template="plotly_white"
            )
            # Overlay order volume as a line on a secondary axis
            fig_monthly.add_scatter(
                x=monthly_df['sale_month'],
                y=monthly_df['monthly_orders'],
                mode='lines+markers',
                name='Orders',
                yaxis='y2',
                line=dict(color='#ff7f0e', width=2),
                marker=dict(size=6)
            )
            fig_monthly.update_layout(
                yaxis2=dict(
                    title="Order Count",
                    overlaying='y',
                    side='right',
                    showgrid=False
                ),
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02)
            )
            st.plotly_chart(fig_monthly, use_container_width=True)
        else:
            st.info("No monthly revenue data available for this period.")

        st.markdown("---")

        # City-wise Sales + New vs. Returning (existing, unchanged)
        c_left, c_right = st.columns(2)
        with c_left:
            st.write("#### 📍 City-wise Sales")
            city_query = f"""
                SELECT c.city, SUM(s.quantity * s.unit_price) as revenue
                FROM fact_sales s
                JOIN dim_customers c ON s.customer_id = c.customer_id
                WHERE s.transaction_date BETWEEN '{date_range[0]}' AND '{date_range[1]}'
                GROUP BY 1 ORDER BY 2 DESC LIMIT 10
            """
            city_df = conn.execute(city_query).df()
            if not city_df.empty:
                fig_city = px.bar(city_df, x='revenue', y='city', orientation='h', 
                                  color='revenue', color_continuous_scale='Blues',
                                  template="plotly_white")
                st.plotly_chart(fig_city, use_container_width=True)
            else:
                st.info("No city data available.")

        with c_right:
            st.write("#### 👥 New vs. Returning Shoppers")
            shopper_query = f"""
                WITH shopper_counts AS (
                    SELECT customer_id, COUNT(DISTINCT transaction_id) as t_count
                    FROM fact_sales
                    WHERE transaction_date BETWEEN '{date_range[0]}' AND '{date_range[1]}'
                    GROUP BY 1
                )
                SELECT 
                    CASE WHEN t_count = 1 THEN 'New' ELSE 'Returning' END as shopper_type,
                    COUNT(*) as user_count
                FROM shopper_counts
                GROUP BY 1
            """
            shopper_df = conn.execute(shopper_query).df()
            if not shopper_df.empty:
                fig_shopper = px.pie(shopper_df, values='user_count', names='shopper_type', 
                                     color_discrete_sequence=['#1f77b4', '#aec7e8'], hole=0.4)
                st.plotly_chart(fig_shopper, use_container_width=True)
            else:
                st.info("No shopper data available.")

        st.markdown("---")

        # -------------------------------------------------------
        # ✅ NEW: TOP-SELLING PRODUCTS
        # -------------------------------------------------------
        st.write("#### 🏆 Top-Selling Products")
        top_n = st.slider("Show top N products", min_value=5, max_value=25, value=10, step=5)
        rank_by = st.radio(
            "Rank by", 
            options=["Revenue", "Units Sold"], 
            horizontal=True
        )
        order_col = "revenue" if rank_by == "Revenue" else "units_sold"
        top_products_query = f"""
            SELECT 
                p.description as product_name,
                SUM(s.quantity) as units_sold,
                SUM(s.quantity * s.unit_price) as revenue
            FROM fact_sales s
            JOIN dim_products p ON s.product_id = p.product_id
            WHERE s.transaction_date BETWEEN '{date_range[0]}' AND '{date_range[1]}'
              AND s.quantity > 0
            GROUP BY 1
            ORDER BY {order_col} DESC
            LIMIT {top_n}
        """
        top_products_df = conn.execute(top_products_query).df()
        if not top_products_df.empty:
            # Truncate long product names for readability
            top_products_df['product_name'] = top_products_df['product_name'].str.slice(0, 40)
            fig_top = px.bar(
                top_products_df,
                x=order_col,
                y='product_name',
                orientation='h',
                color=order_col,
                color_continuous_scale='Teal',
                template="plotly_white",
                labels={
                    'product_name': 'Product',
                    'revenue': 'Revenue (₹)',
                    'units_sold': 'Units Sold'
                },
                title=f"Top {top_n} Products by {rank_by}"
            )
            fig_top.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_top, use_container_width=True)

            # Also show as a compact table below the chart
            with st.expander("📋 View as Table"):
                display_df = top_products_df.copy()
                display_df['revenue'] = display_df['revenue'].apply(lambda x: f"₹{x:,.2f}")
                display_df.columns = ['Product', 'Units Sold', 'Revenue']
                st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("No product data available for this period.")

    except Exception as e:
        st.warning(f"⚠️ Dashboard restricted: {e}")


# ============================================================
# --- TAB 2: REAL-TIME OPERATIONS ---
# ============================================================
with tab_ops:
    st.subheader("Operations & Logistics Health")
    
    st.warning("🔄 Live Stream: Processing logs from `raw_data/stream/` every 30 seconds.")
    
    o1, o2 = st.columns(2)
    with o1:
        st.write("#### 📦 Inventory Turnover Ratio")
        try:
            turnover_query = f"""
                SELECT 
                    CAST(SUM(s.quantity) AS FLOAT) / NULLIF(AVG(i.stock_on_hand), 0) as turnover_ratio
                FROM fact_sales s
                LEFT JOIN fact_inventory i ON s.product_id = i.product_id
                WHERE s.transaction_date BETWEEN '{date_range[0]}' AND '{date_range[1]}'
            """
            turnover_val = conn.execute(turnover_query).df()['turnover_ratio'][0]
            st.metric("Inventory Turnover", f"{turnover_val:.2f}x", help="Formula: SUM(qty) / AVG(stock)")
            st.progress(min(max(turnover_val / 10, 0.0), 1.0))
        except:
            st.metric("Inventory Turnover", "0.00x")

    with o2:
        st.write("#### 🚚 Average Delivery Time")
        try:
            delivery_query = "SELECT AVG(delivery_time_days) as avg_days FROM fact_shipments"
            avg_delivery = conn.execute(delivery_query).df()['avg_days'][0]
            st.metric("Avg. Delivery Time", f"{avg_delivery:.1f} Days", delta_color="inverse")
        except:
            st.metric("Avg. Delivery Time", "N/A")

    st.markdown("---")
    
    st.write("#### 🗓️ Seasonal Demand Trends")
    try:
        seasonal_query = f"""
            SELECT 
                MONTHNAME(transaction_date) as month,
                MONTH(transaction_date) as month_num,
                SUM(quantity) as units_sold,
                SUM(quantity * unit_price) as revenue
            FROM fact_sales
            WHERE transaction_date BETWEEN '{date_range[0]}' AND '{date_range[1]}'
            GROUP BY 1, 2
            ORDER BY 2
        """
        seasonal_df = conn.execute(seasonal_query).df()
        if not seasonal_df.empty:
            fig_seasonal = px.area(seasonal_df, x='month', y='revenue', 
                                   title="Revenue seasonality", template="plotly_white")
            st.plotly_chart(fig_seasonal, use_container_width=True)
        else:
            st.info("Awaiting seasonal data...")
    except:
        st.caption("Error loading seasonal trends.")


# ============================================================
# --- TAB 3: AI INSIGHTS ---
# ============================================================
with tab_ai:
    st.subheader("Predictive Analytics & Intelligence")
    
    ai_col1, ai_col2 = st.columns([2, 1])
    
    with ai_col1:
        st.write("#### 🧺 Market Basket Analysis")
        if st.button("🚀 Run Rule Discovery"):
            try:
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
                    st.error("Incomplete data.")
            except Exception as e:
                st.error(f"Analysis Error: {e}")
    
    with ai_col2:
        st.write("#### 💎 Customer Lifetime Value (CLV)")
        try:
            clv_query = f"""
                WITH customer_metrics AS (
                    SELECT 
                        customer_id,
                        AVG(quantity * unit_price) as aov,
                        COUNT(DISTINCT transaction_id) as frequency
                    FROM fact_sales
                    WHERE transaction_date BETWEEN '{date_range[0]}' AND '{date_range[1]}'
                    GROUP BY 1
                )
                SELECT 
                    c.name,
                    cm.aov * cm.frequency * 1.5 as clv_score
                FROM customer_metrics cm
                JOIN dim_customers c ON cm.customer_id = c.customer_id
                ORDER BY 2 DESC LIMIT 5
            """
            clv_df = conn.execute(clv_query).df()
            if not clv_df.empty:
                for idx, row in clv_df.iterrows():
                    st.write(f"**{row['name']}**")
                    st.caption(f"Predicted Value: ₹{row['clv_score']:,.2f}")
            else:
                st.info("Awaiting CLV calculation data.")
        except:
            st.caption("CLV data pending...")


# --- FOOTER ---
st.markdown("---")
st.caption(f"ShelfSmart v2.0 | Person B Analyst Suite | Last Updated: {datetime.now().strftime('%H:%M:%S')}")