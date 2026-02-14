import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import numpy as np
from src.db_connector import initialize_analytics_db
from src.ml_logic import run_market_basket_analysis
import random
import os



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
st.sidebar.markdown("### Select the Date Range for Analysis")
st.sidebar.markdown("---")

# Date Range Section with better visual grouping
st.sidebar.markdown("#### 📅 Date Range")
col1, col2 = st.sidebar.columns(2)
with col1:
    start_date = st.date_input(
        "From",
        datetime(2010, 12, 1),
        help="Select start date for analysis"
    )
with col2:
    end_date = st.date_input(
        "To",
        datetime(2011, 12, 9),
        help="Select end date for analysis"
    )
date_range = [start_date, end_date]

# Display selected range in a more visual way
date_diff = (end_date - start_date).days
st.sidebar.caption(f"📊 Analysis Period: **{date_diff} days**")

st.sidebar.markdown("---")

# Enhanced System Status with better formatting
st.sidebar.markdown("#### 🔧 System Status")

# Create status indicators with color coding
status_html = """
<div style="padding: 10px; border-radius: 5px; background-color: #0e1117;">
    <div style="margin-bottom: 8px;">
        <span style="color: #00ff00; font-size: 16px;">●</span>
        <span style="margin-left: 8px;"><strong>Ingestion:</strong> Active</span>
    </div>
    <div style="margin-bottom: 8px;">
        <span style="color: #00ff00; font-size: 16px;">●</span>
        <span style="margin-left: 8px;"><strong>Storage:</strong> Parquet (Local)</span>
    </div>
    <div>
        <span style="color: #00ff00; font-size: 16px;">●</span>
        <span style="margin-left: 8px;"><strong>Compute:</strong> DuckDB</span>
    </div>
</div>
"""
st.sidebar.markdown(status_html, unsafe_allow_html=True)

st.sidebar.markdown("---")

# Optional: Add data refresh timestamp
st.sidebar.caption(f"🕐 Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# --- MAIN UI ---
# Option 1: Using an image file (if you have a logo/icon)
col1, col2 = st.columns([1, 10])
with col1:
    st.image("assests/images.png", width=80)  # Replace with your image path
with col2:
    st.markdown(
        """
        <h1 style="
            font-family: 'Georgia', 'Palatino', serif;
            font-size: 46px;
            font-weight: 700;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-top: 10px;
            letter-spacing: 1px;
        ">
            ShelfSmart: Intelligent Retail Hub
        </h1>
        """,
        unsafe_allow_html=True
    )




st.markdown("""
<style>
.stTabs [data-baseweb="tab-list"] {
    gap: 2px;
    background: transparent;
    border-bottom: 2px solid #2d3748;
    padding: 0;
}

.stTabs [data-baseweb="tab"] {
    height: 60px;
    padding: 0px 32px;
    background: transparent;
    border-radius: 0;
    border-bottom: 3px solid transparent;
    color: #8b95a8;
    font-size: 20px;
    font-weight: 600;
    transition: all 0.3s ease;
    position: relative;
}

.stTabs [data-baseweb="tab"]::after {
    content: '';
    position: absolute;
    bottom: -2px;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, #3b82f6, #60a5fa);
    transform: scaleX(0);
    transition: transform 0.3s ease;
}

.stTabs [data-baseweb="tab"]:hover {
    color: #c3cad8;
    background: rgba(59, 130, 246, 0.05);
}

.stTabs [data-baseweb="tab"]:hover::after {
    transform: scaleX(0.5);
}

.stTabs [aria-selected="true"] {
    color: #60a5fa !important;
    background: transparent;
    font-weight: 700;
}

.stTabs [aria-selected="true"]::after {
    transform: scaleX(1);
}
</style>
""", unsafe_allow_html=True)

tab_exec, tab_ops, tab_ai = st.tabs([
    "📈 Executive Summary", 
    "🚚 Real-Time Operations", 
    "🤖 AI Insights"
])

# ============================================================
# --- TAB 1: EXECUTIVE SUMMARY ---
# ============================================================
with tab_exec:
    # Standardized heading styles
    st.markdown("""
    <style>
    .section-header {
        font-size: 18px;
        font-weight: 600;
        color: #e2e8f0;
        margin-top: 32px;
        margin-bottom: 20px;
        padding: 0;
    }
    .main-section-title {
        font-size: 24px;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 32px;
        margin-top: 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Main section title
    st.markdown('<div class="main-section-title">Commercial Performance Metrics</div>', unsafe_allow_html=True)
    
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

        rev = metrics_df['total_rev'][0] if not metrics_df.empty else 0
        orders = metrics_df['total_orders'][0] if not metrics_df.empty else 0
        aov = metrics_df['avg_order_val'][0] if not metrics_df.empty else 0

        # Gradient Boxes with Icons
        st.markdown("""
        <style>
        .metric-card {
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
            padding: 25px;
            border-radius: 15px;
            border-left: 5px solid;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease;
        }
        .metric-card:hover {
            transform: translateY(-5px);
        }
        .metric-value {
            font-size: 32px;
            font-weight: bold;
            margin: 10px 0;
        }
        .metric-label {
            color: #888;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .metric-delta {
            font-size: 14px;
            font-weight: 600;
            margin-top: 8px;
        }
        .positive { color: #10b981; }
        .negative { color: #ef4444; }
        </style>
        """, unsafe_allow_html=True)

        m1, m2, m3, m4 = st.columns([1.2, 1, 1, 0.9])

        with m1:
            st.markdown(f"""
            <div class="metric-card" style="border-left-color: #3b82f6;">
                <div class="metric-label">💰 Total Revenue</div>
                <div class="metric-value">₹{rev:,.2f}</div>
                <div class="metric-delta positive">↗ +5.2%</div>
            </div>
            """, unsafe_allow_html=True)

        with m2:
            st.markdown(f"""
            <div class="metric-card" style="border-left-color: #8b5cf6;">
                <div class="metric-label">📦 Order Volume</div>
                <div class="metric-value">{orders:,}</div>
                <div class="metric-delta negative">↘ -1.4%</div>
            </div>
            """, unsafe_allow_html=True)

        with m3:
            st.markdown(f"""
            <div class="metric-card" style="border-left-color: #06b6d4;">
                <div class="metric-label">🛍️ Avg. Order Value</div>
                <div class="metric-value">₹{aov:,.2f}</div>
                <div class="metric-delta positive">↗ +0.8%</div>
            </div>
            """, unsafe_allow_html=True)

        with m4:
            try:
                delivery_query = "SELECT AVG(delivery_time_days) as avg_days FROM fact_shipments"
                avg_delivery = conn.execute(delivery_query).df()['avg_days'][0]
                st.markdown(f"""
                <div class="metric-card" style="border-left-color: #10b981;">
                    <div class="metric-label">🚚 Avg. Delivery Time</div>
                    <div class="metric-value">{avg_delivery:.1f} Days</div>
                </div>
                """, unsafe_allow_html=True)
            except:
                st.markdown(f"""
                <div class="metric-card" style="border-left-color: #10b981;">
                    <div class="metric-label">🚚 Avg. Delivery Time</div>
                    <div class="metric-value">N/A</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")

        # -------------------------------------------------------
        # ✅ DAILY REVENUE TREND
        # -------------------------------------------------------
        st.markdown('<div class="section-header" style="font-size: 24px; font-weight: bold;"> Daily Revenue Trend</div>', unsafe_allow_html=True)

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
                labels={'sale_date': 'Date', 'daily_revenue': 'Revenue (₹)'},
                template="plotly_white"
            )
            fig_daily.update_traces(line_color='#3b82f6', line_width=2.5)
            fig_daily.update_layout(
                hovermode="x unified",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#e2e8f0', size=12),
                showlegend=False,
                margin=dict(t=20, b=40, l=40, r=40),
                xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
                yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
            )
            st.plotly_chart(fig_daily, use_container_width=True)
        else:
            st.info("No daily revenue data available for this period.")

        # -------------------------------------------------------
        # ✅ MONTHLY REVENUE TREND
        # -------------------------------------------------------
        st.markdown('<div class="section-header" style="font-size: 24px; font-weight: bold;"> Monthly Revenue Trend</div>', unsafe_allow_html=True)
        
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
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
                margin=dict(t=20, b=40, l=40, r=40)
            )
            st.plotly_chart(fig_monthly, use_container_width=True)
        else:
            st.info("No monthly revenue data available for this period.")

        st.markdown("---")

        # City-wise Sales + New vs. Returning
        c_left, c_right = st.columns(2)
        with c_left:
            st.markdown('<div class="section-header" style="font-size: 24px; font-weight: bold;">📍 City-wise Sales</div>', unsafe_allow_html=True)
            
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
                fig_city.update_layout(margin=dict(t=20, b=40, l=40, r=40))
                st.plotly_chart(fig_city, use_container_width=True)
            else:
                st.info("No city data available.")

        with c_right:
            st.markdown('<div class="section-header" style="font-size: 24px; font-weight: bold;">👥 New vs. Returning Shoppers</div>', unsafe_allow_html=True)
            
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
                fig_shopper.update_layout(margin=dict(t=20, b=40, l=40, r=40))
                st.plotly_chart(fig_shopper, use_container_width=True)
            else:
                st.info("No shopper data available.")

        st.markdown("---")

        # -------------------------------------------------------
        # ✅ TOP-SELLING PRODUCTS
        # -------------------------------------------------------
        st.markdown('<div class="section-header" style="font-size: 24px; font-weight: bold;">🏆 Top-Selling Products</div>', unsafe_allow_html=True)
        
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
                }
            )
            fig_top.update_layout(
                yaxis={'categoryorder': 'total ascending'},
                margin=dict(t=20, b=40, l=40, r=40)
            )
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
    st.write(" Real-Time Operations Center")
    
    # High-Frequency Fragment (Refreshes every 1 second)
    @st.fragment(run_every=1)
    def live_chart_section():
        file_path = "raw_data/stream/live_stream.csv"
        
        if os.path.exists(file_path):
            # Read the last 30 seconds of data for the moving chart
            cols = ['timestamp', 'sales', 'inventory', 'store_id']
            df = pd.read_csv(file_path, names=cols).tail(15)
            
            # Layout: Metric + Chart
            m1, m2 = st.columns([1, 3])
            with m1:
                current_val = df['sales'].iloc[-1]
                st.metric(label="Live Sales (INR)", value=f"₹{current_val}")
                
                st.write("📝 Latest Logs")
                st.dataframe(df.tail(5), hide_index=True)
            
            with m2:
                # The moving line chart
                st.line_chart(df, x="timestamp", y="sales", color="#ff4b4b")
        else:
            st.warning(" Waiting for stream... Please run the generator in your terminal.")

    # Call the live section
    live_chart_section()
    
    st.markdown("---")
    
    st.write("####  Seasonal Demand Trends")
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
    #st.markdown('<div class="main-section-title">Predictive Analytics & Intelligence</div>', unsafe_allow_html=True)
    
    ai_col1, ai_col2 = st.columns([2, 1])
    
    with ai_col1:
        st.markdown('<div class="section-header">🧺 Product Pairing Insights</div>', unsafe_allow_html=True)
        st.caption("Discover which products customers frequently buy together")
        
        if st.button("🚀 Discover Product Pairs"):
            try:
                ml_data = conn.execute("""
                    SELECT s.transaction_id, p.description as product_name
                    FROM fact_sales s
                    JOIN dim_products p ON s.product_id = p.product_id
                    WHERE s.quantity > 0
                """).df()
                if not ml_data.empty:
                    rules = run_market_basket_analysis(ml_data)
                    
                    if not rules.empty:
                        # Show top rules based on lift
                        top_rules = rules.nlargest(15, 'lift')
                        
                        # Create a simplified business-friendly dataframe
                        business_rules = top_rules.copy()
                        business_rules['buy_frequency'] = (business_rules['support'] * 100).round(1)
                        business_rules['purchase_likelihood'] = (business_rules['confidence'] * 100).round(0)
                        business_rules['strength_score'] = business_rules['lift'].round(1)
                        
                        # Create tabs for different views
                        viz_tab1, viz_tab2, viz_tab3 = st.tabs(["💡 Key Insights", "📊 Visual Analysis", "🎁 Recommendations"])
                        
                        with viz_tab1:
                            st.markdown("### 🎯 Top Product Combinations")
                            st.markdown("---")
                            
                            # Show top 5 insights as cards
                            for idx, row in business_rules.head(5).iterrows():
                                col1, col2 = st.columns([3, 1])
                                with col1:
                                    st.markdown(f"""
                                    <div style="background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%); 
                                                padding: 20px; border-radius: 10px; border-left: 4px solid #3b82f6; margin-bottom: 15px;">
                                        <div style="font-size: 16px; font-weight: 600; color: #60a5fa; margin-bottom: 8px;">
                                            🛒 Customers who buy: <span style="color: #ffffff;">{row['antecedents']}</span>
                                        </div>
                                        <div style="font-size: 14px; color: #94a3b8; margin-bottom: 12px;">
                                            Also tend to buy: <span style="color: #10b981; font-weight: 600;">{row['consequents']}</span>
                                        </div>
                                        <div style="font-size: 13px; color: #8b95a8;">
                                            📈 {int(row['purchase_likelihood'])}% of customers who bought the first item also bought the second
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                with col2:
                                    st.metric(
                                        "Strength", 
                                        f"{row['strength_score']}x",
                                        help="How much more likely this combination occurs vs random chance. Higher = stronger relationship"
                                    )
                        
                        with viz_tab2:
                            # Simple bar chart with business language
                            fig_simple = px.bar(
                                business_rules.head(10),
                                y='antecedents',
                                x='purchase_likelihood',
                                color='strength_score',
                                orientation='h',
                                labels={
                                    'antecedents': 'When Customers Buy',
                                    'purchase_likelihood': 'Likelihood They Also Buy Related Item (%)',
                                    'strength_score': 'Relationship Strength'
                                },
                                color_continuous_scale='Blues'
                            )
                            fig_simple.update_layout(
                                height=500,
                                margin=dict(t=20, b=40, l=200, r=40),
                                yaxis={'categoryorder': 'total ascending'}
                            )
                            st.plotly_chart(fig_simple, use_container_width=True)
                            
                            st.info(" The longer the bar, the more likely customers are to buy both products together. Darker colors mean stronger relationships.")
                        
                        with viz_tab3:
                            st.markdown("### 🎁 Actionable Recommendations")
                            st.markdown("---")
                            
                            # Generate business recommendations
                            recommendations = [
                                {
                                    "icon": "🏪",
                                    "title": "Store Layout",
                                    "text": f"Place **{business_rules.iloc[0]['antecedents']}** near **{business_rules.iloc[0]['consequents']}** to increase impulse purchases."
                                },
                                {
                                    "icon": "🎯",
                                    "title": "Cross-Sell Promotions",
                                    "text": f"Create a bundle offer: Buy **{business_rules.iloc[1]['antecedents']}**, get a discount on **{business_rules.iloc[1]['consequents']}**."
                                },
                                {
                                    "icon": "📧",
                                    "title": "Email Marketing",
                                    "text": f"Send personalized recommendations to customers who bought **{business_rules.iloc[2]['antecedents']}** suggesting **{business_rules.iloc[2]['consequents']}**."
                                },
                                {
                                    "icon": "📦",
                                    "title": "Inventory Planning",
                                    "text": f"When stocking **{business_rules.iloc[0]['antecedents']}**, ensure adequate inventory of **{business_rules.iloc[0]['consequents']}**."
                                }
                            ]
                            
                            for rec in recommendations:
                                st.markdown(f"""
                                <div style="background: rgba(16, 185, 129, 0.1); padding: 15px; border-radius: 8px; 
                                            border-left: 3px solid #10b981; margin-bottom: 12px;">
                                    <div style="font-size: 18px; margin-bottom: 5px;">{rec['icon']} <strong>{rec['title']}</strong></div>
                                    <div style="font-size: 14px; color: #cbd5e1;">{rec['text']}</div>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            # Show simple table
                            st.markdown("---")
                            st.markdown("### 📋 Complete Pairing List")
                            simple_table = business_rules[['antecedents', 'consequents', 'purchase_likelihood', 'strength_score']].copy()
                            simple_table.columns = ['Customers Buy This', 'They Also Buy This', 'Likelihood (%)', 'Strength']
                            simple_table['Likelihood (%)'] = simple_table['Likelihood (%)'].astype(int).astype(str) + '%'
                            simple_table['Strength'] = simple_table['Strength'].astype(str) + 'x'
                            st.dataframe(simple_table, use_container_width=True, hide_index=True)
                    else:
                        st.warning("No significant product pairings found in the current data.")
                else:
                    st.error("Incomplete data.")
            except Exception as e:
                st.error(f"Analysis Error: {e}")
    
    with ai_col2:
        st.markdown('<div class="section-header">💎 Top Customers by Value</div>', unsafe_allow_html=True)
        st.caption("Customers with highest predicted lifetime value")
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
                ORDER BY 2 DESC LIMIT 8
            """
            clv_df = conn.execute(clv_query).df()
            if not clv_df.empty:
                # Show as a mini leaderboard
                for idx, row in clv_df.iterrows():
                    rank = idx + 1
                    medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"#{rank}"
                    st.markdown(f"""
                    <div style="background: rgba(59, 130, 246, 0.05); padding: 12px; border-radius: 8px; margin-bottom: 8px;">
                        <div style="font-size: 16px; font-weight: 600; color: #e2e8f0;">
                            {medal} {row['name']}
                        </div>
                        <div style="font-size: 13px; color: #10b981; margin-top: 4px;">
                            Expected Value: ₹{row['clv_score']:,.0f}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.info(" Focus retention efforts on these high-value customers through loyalty programs and personalized offers.")
            else:
                st.info("Awaiting customer value data.")
        except:
            st.caption("Customer value analysis pending...")


# --- FOOTER ---
st.markdown("---")
st.caption(f"ShelfSmart | Last Updated: {datetime.now().strftime('%H:%M:%S')}")