# ShelfSmart Analytics Queries Documentation

## 1. COMMERCIAL METRICS

### 1.1 Daily Revenue
**Purpose:** Track revenue trends on a daily basis over the selected period
```sql
SELECT 
    CAST(transaction_date AS DATE) as sale_date,
    SUM(quantity * unit_price) as daily_revenue
FROM fact_sales
WHERE transaction_date BETWEEN '{start_date}' AND '{end_date}'
GROUP BY 1
ORDER BY 1
```

**Output Columns:**
- `sale_date`: Date of transactions
- `daily_revenue`: Total revenue for that day

---

### 1.2 Monthly Revenue
**Purpose:** Analyze revenue and order volume on a monthly basis
```sql
SELECT 
    STRFTIME(transaction_date, '%Y-%m') as sale_month,
    SUM(quantity * unit_price) as monthly_revenue,
    COUNT(DISTINCT transaction_id) as monthly_orders
FROM fact_sales
WHERE transaction_date BETWEEN '{start_date}' AND '{end_date}'
GROUP BY 1
ORDER BY 1
```

**Output Columns:**
- `sale_month`: Month in YYYY-MM format
- `monthly_revenue`: Total revenue for the month
- `monthly_orders`: Number of unique orders in the month

---

### 1.3 City-wise Sales
**Purpose:** Identify top-performing cities by revenue
```sql
SELECT 
    c.city, 
    SUM(s.quantity * s.unit_price) as revenue
FROM fact_sales s
JOIN dim_customers c ON s.customer_id = c.customer_id
WHERE s.transaction_date BETWEEN '{start_date}' AND '{end_date}'
GROUP BY 1 
ORDER BY 2 DESC 
LIMIT 10
```

**Output Columns:**
- `city`: City name
- `revenue`: Total revenue generated from that city

---

### 1.4 Top-Selling Products
**Purpose:** Identify best-performing products by revenue or units sold
```sql
SELECT 
    p.description as product_name,
    SUM(s.quantity) as units_sold,
    SUM(s.quantity * s.unit_price) as revenue
FROM fact_sales s
JOIN dim_products p ON s.product_id = p.product_id
WHERE s.transaction_date BETWEEN '{start_date}' AND '{end_date}'
  AND s.quantity > 0
GROUP BY 1
ORDER BY {revenue|units_sold} DESC
LIMIT {top_n}
```

**Output Columns:**
- `product_name`: Product description
- `units_sold`: Total quantity sold
- `revenue`: Total revenue generated

**Parameters:**
- `{revenue|units_sold}`: Order by revenue or units_sold based on user selection
- `{top_n}`: Number of top products to show (5-25)

---

### 1.5 High-Level KPIs
**Purpose:** Calculate summary metrics for the executive dashboard
```sql
SELECT 
    SUM(quantity * unit_price) as total_rev,
    COUNT(DISTINCT transaction_id) as total_orders,
    AVG(quantity * unit_price) as avg_order_val
FROM fact_sales
WHERE transaction_date BETWEEN '{start_date}' AND '{end_date}'
```

**Output Columns:**
- `total_rev`: Total revenue for the period
- `total_orders`: Total number of unique orders
- `avg_order_val`: Average order value

---

## 2. OPERATIONS METRICS

### 2.1 Average Delivery Time
**Purpose:** Monitor logistics performance
```sql
SELECT 
    AVG(delivery_time_days) as avg_days 
FROM fact_shipments
```

**Output Columns:**
- `avg_days`: Average delivery time in days

---

### 2.2 Seasonal Demand Trends
**Purpose:** Identify seasonal patterns in sales
```sql
SELECT 
    MONTHNAME(transaction_date) as month,
    MONTH(transaction_date) as month_num,
    SUM(quantity) as units_sold,
    SUM(quantity * unit_price) as revenue
FROM fact_sales
WHERE transaction_date BETWEEN '{start_date}' AND '{end_date}'
GROUP BY 1, 2
ORDER BY 2
```

**Output Columns:**
- `month`: Month name (e.g., "January")
- `month_num`: Month number (1-12) for sorting
- `units_sold`: Total units sold in that month
- `revenue`: Total revenue for that month

---

### 2.3 Inventory Turnover Ratio
**Purpose:** Measure how efficiently inventory is being sold
**Status:** Removed from current implementation due to formula accuracy issues

**Original Query (For Reference):**
```sql
-- DEPRECATED: Removed due to incorrect calculation
WITH avg_inventory AS (
    SELECT AVG(stock_on_hand) as avg_stock
    FROM fact_inventory
    WHERE inventory_date BETWEEN '{start_date}' AND '{end_date}'
)
SELECT 
    CAST(SUM(s.quantity) AS FLOAT) / NULLIF(ai.avg_stock, 0) as turnover_ratio
FROM fact_sales s
CROSS JOIN avg_inventory ai
WHERE s.transaction_date BETWEEN '{start_date}' AND '{end_date}'
```

---

## 3. CUSTOMER METRICS

### 3.1 New vs. Returning Shoppers
**Purpose:** Segment customers based on purchase behavior
```sql
WITH shopper_counts AS (
    SELECT 
        customer_id, 
        COUNT(DISTINCT transaction_id) as t_count
    FROM fact_sales
    WHERE transaction_date BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY 1
)
SELECT 
    CASE 
        WHEN t_count = 1 THEN 'New' 
        ELSE 'Returning' 
    END as shopper_type,
    COUNT(*) as user_count
FROM shopper_counts
GROUP BY 1
```

**Output Columns:**
- `shopper_type`: "New" or "Returning"
- `user_count`: Number of customers in each category

**Business Logic:**
- New: Customers with exactly 1 transaction in the period
- Returning: Customers with 2+ transactions in the period

---

### 3.2 Customer Lifetime Value (CLV)
**Purpose:** Identify high-value customers for retention strategies
```sql
WITH customer_metrics AS (
    SELECT 
        customer_id,
        AVG(quantity * unit_price) as aov,
        COUNT(DISTINCT transaction_id) as frequency
    FROM fact_sales
    WHERE transaction_date BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY 1
)
SELECT 
    c.name,
    cm.aov * cm.frequency * 1.5 as clv_score
FROM customer_metrics cm
JOIN dim_customers c ON cm.customer_id = c.customer_id
ORDER BY 2 DESC 
LIMIT {top_n}
```

**Output Columns:**
- `name`: Customer name
- `clv_score`: Predicted lifetime value

**Formula:**
```
CLV = Average Order Value × Purchase Frequency × 1.5 (retention multiplier)
```

**Parameters:**
- `{top_n}`: Number of top customers to show (typically 5-8)

---

### 3.3 Market Basket Analysis
**Purpose:** Discover product associations and cross-selling opportunities

**Data Extraction Query:**
```sql
SELECT 
    s.transaction_id, 
    p.description as product_name
FROM fact_sales s
JOIN dim_products p ON s.product_id = p.product_id
WHERE s.quantity > 0
```

**Python Analysis:**
```python
def run_market_basket_analysis(ml_data):
    """
    Performs association rule mining to find frequently bought together items
    
    Parameters:
    ml_data (DataFrame): Contains transaction_id and product_name columns
    
    Returns:
    DataFrame: Association rules with antecedents, consequents, support, confidence, lift
    """
    from mlxtend.frequent_patterns import apriori, association_rules
    from mlxtend.preprocessing import TransactionEncoder
    
    # Group products by transaction
    transactions = ml_data.groupby('transaction_id')['product_name'].apply(list).values
    
    # Encode transactions
    te = TransactionEncoder()
    te_ary = te.fit(transactions).transform(transactions)
    df = pd.DataFrame(te_ary, columns=te.columns_)
    
    # Find frequent itemsets (support >= 0.01 = appears in 1% of transactions)
    frequent_itemsets = apriori(df, min_support=0.01, use_colnames=True)
    
    # Generate association rules (confidence >= 0.1 = 10% likelihood)
    rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=0.1)
    
    # Convert frozensets to strings for display
    rules['antecedents'] = rules['antecedents'].apply(lambda x: ', '.join(list(x)))
    rules['consequents'] = rules['consequents'].apply(lambda x: ', '.join(list(x)))
    
    return rules[['antecedents', 'consequents', 'support', 'confidence', 'lift']]
```

**Output Columns:**
- `antecedents`: Product(s) bought first
- `consequents`: Product(s) bought together
- `support`: Frequency of the combination (0-1)
- `confidence`: Likelihood of buying consequent when antecedent is bought (0-1)
- `lift`: Strength of association (>1 = positive association)

**Business Metrics (Calculated from Results):**
```python
# Convert technical metrics to business-friendly format
business_rules['buy_frequency'] = (rules['support'] * 100).round(1)
business_rules['purchase_likelihood'] = (rules['confidence'] * 100).round(0)
business_rules['strength_score'] = rules['lift'].round(1)
```

---

## 4. REAL-TIME OPERATIONS

### 4.1 Live Sales Stream
**Purpose:** Monitor real-time sales activity

**Python Code:**
```python
@st.fragment(run_every=1)  # Refresh every 1 second
def live_chart_section():
    file_path = "raw_data/stream/live_stream.csv"
    
    if os.path.exists(file_path):
        # Read the last 30 seconds of data
        cols = ['timestamp', 'sales', 'inventory', 'store_id']
        df = pd.read_csv(file_path, names=cols).tail(15)
        
        # Get current sales value
        current_val = df['sales'].iloc[-1]
        
        return df, current_val
```

**Data Format:**
- `timestamp`: Time of transaction
- `sales`: Sales value in INR
- `inventory`: Current inventory level
- `store_id`: Store identifier

---



### Revenue Calculation
```
Revenue = quantity × unit_price
```

### CLV Calculation
```
CLV = Average Order Value × Purchase Frequency × 1.5
```
The 1.5 multiplier is a retention factor assuming customer continues purchasing.

### New Customer Definition
A customer is "New" if they have exactly 1 transaction in the analysis period.

### Market Basket Thresholds
- Minimum Support: 1% (appears in at least 1% of transactions)
- Minimum Confidence: 10% (at least 10% likelihood of association)
- Rules sorted by Lift (strength of association)

---

