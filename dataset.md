# ShelfSmart Analytical Dataset Documentation

## Overview
This document describes the transformation from the raw `online_retail.csv` dataset into cleaned, structured analytical tables ready for database ingestion and analysis.

---

## 1. SOURCE DATA

### Raw Dataset: `online_retail.csv`

**Schema:**
```
InvoiceNo, StockCode, Description, Quantity, InvoiceDate, UnitPrice, CustomerID, Country
```

**Sample Raw Data:**
```csv
InvoiceNo,StockCode,Description,Quantity,InvoiceDate,UnitPrice,CustomerID,Country
536365,85123A,WHITE HANGING HEART T-LIGHT HOLDER,6,2010-12-01 08:26:00,2.55,17850,United Kingdom
536365,71053,WHITE METAL LANTERN,6,2010-12-01 08:26:00,3.39,17850,United Kingdom
536365,84406B,CREAM CUPID HEARTS COAT HANGER,8,2010-12-01 08:26:00,2.75,17850,United Kingdom
536366,22633,HAND WARMER UNION JACK,6,2010-12-01 08:28:00,1.85,17850,United Kingdom
536367,84879,ASSORTED COLOUR BIRD ORNAMENT,32,2010-12-01 08:34:00,1.69,13047,United Kingdom
C536379,D,Discount,-1,2010-12-01 09:41:00,27.50,14527,United Kingdom
536380,22960,JAM MAKING SET WITH JARS,12,2010-12-01 09:41:00,4.25,14527,United Kingdom
```

**Data Quality Issues in Raw Data:**
- Missing CustomerIDs
- Negative quantities (returns/cancellations marked with 'C' prefix in InvoiceNo)
- Inconsistent descriptions
- No standardized store or shipment information
- Country field needs normalization to city

---

## 2. CLEANED ANALYTICAL TABLES

### 2.1 Dimension Table: `dim_customers.csv`

**Purpose:** Master customer information with unique customer records

**Schema:**
| Column Name | Data Type | Description | Constraints |
|-------------|-----------|-------------|-------------|
| customer_id | VARCHAR(10) | Unique customer identifier | PRIMARY KEY, NOT NULL |
| name | VARCHAR(100) | Customer full name | NOT NULL |
| email | VARCHAR(150) | Customer email address | UNIQUE |
| city | VARCHAR(100) | Customer city location | NOT NULL |
| update_timestamp | TIMESTAMP | Last update timestamp | NOT NULL |

**Sample Data:**
```csv
customer_id,name,email,city,update_timestamp
CUST17850,Rajesh Kumar,rajesh.kumar@email.com,Mumbai,2024-01-15 10:30:00
CUST13047,Priya Sharma,priya.sharma@email.com,Delhi,2024-01-15 10:31:00
CUST14527,Amit Patel,amit.patel@email.com,Ahmedabad,2024-01-15 10:32:00
CUST15311,Sneha Reddy,sneha.reddy@email.com,Hyderabad,2024-01-15 10:33:00
CUST16250,Vikram Singh,vikram.singh@email.com,Bangalore,2024-01-15 10:34:00
CUST12583,Anita Desai,anita.desai@email.com,Pune,2024-01-15 10:35:00
CUST13748,Rahul Verma,rahul.verma@email.com,Chennai,2024-01-15 10:36:00
CUST14096,Deepa Nair,deepa.nair@email.com,Kochi,2024-01-15 10:37:00
CUST15769,Karan Mehta,karan.mehta@email.com,Surat,2024-01-15 10:38:00
CUST17677,Lakshmi Iyer,lakshmi.iyer@email.com,Coimbatore,2024-01-15 10:39:00
```



---

### 2.2 Dimension Table: `dim_products.csv`

**Purpose:** Product catalog with pricing and category information

**Schema:**
| Column Name | Data Type | Description | Constraints |
|-------------|-----------|-------------|-------------|
| product_id | VARCHAR(10) | Unique product identifier | PRIMARY KEY, NOT NULL |
| description | VARCHAR(500) | Product description | NOT NULL |
| base_price | DECIMAL(10,2) | Standard product price | NOT NULL, CHECK (base_price > 0) |
| category | VARCHAR(100) | Product category | NOT NULL |
| supplier_id | VARCHAR(10) | Supplier identifier | NOT NULL |

**Sample Data:**
```csv
product_id,description,base_price,category,supplier_id
PROD85123A,WHITE HANGING HEART T-LIGHT HOLDER,2.55,Home Decor,SUP001
PROD71053,WHITE METAL LANTERN,3.39,Home Decor,SUP001
PROD84406B,CREAM CUPID HEARTS COAT HANGER,2.75,Home Decor,SUP002
PROD22633,HAND WARMER UNION JACK,1.85,Gifts,SUP003
PROD84879,ASSORTED COLOUR BIRD ORNAMENT,1.69,Home Decor,SUP001
PROD22960,JAM MAKING SET WITH JARS,4.25,Kitchen,SUP004
PROD21730,GLASS STAR FROSTED T-LIGHT HOLDER,1.25,Home Decor,SUP001
PROD22423,REGENCY CAKESTAND 3 TIER,12.75,Kitchen,SUP004
PROD85099B,JUMBO BAG RED RETROSPOT,1.95,Bags,SUP005
PROD22086,PAPER CHAIN KIT 50'S CHRISTMAS,2.55,Party,SUP003
PROD84029E,RED WOOLLY HOTTIE WHITE HEART,3.75,Gifts,SUP002
PROD22111,SCOTTIE DOG HOT WATER BOTTLE,4.95,Gifts,SUP002
PROD21034,RED RETROSPOT CHARLOTTE BAG,4.15,Bags,SUP005
PROD22616,PACK OF 12 LONDON TISSUES,0.85,Gifts,SUP003
PROD22492,MINI PAINT SET VINTAGE,0.65,Toys,SUP006
```


---

### 2.3 Dimension Table: `dim_stores.csv`

**Purpose:** Store location master data

**Schema:**
| Column Name | Data Type | Description | Constraints |
|-------------|-----------|-------------|-------------|
| store_id | VARCHAR(10) | Unique store identifier | PRIMARY KEY, NOT NULL |
| store_name | VARCHAR(100) | Store name | NOT NULL |
| city | VARCHAR(100) | Store city location | NOT NULL |

**Sample Data:**
```csv
store_id,store_name,city
STORE001,ShelfSmart Mumbai Central,Mumbai
STORE002,ShelfSmart Delhi Main,Delhi
STORE003,ShelfSmart Bangalore Hub,Bangalore
STORE004,ShelfSmart Chennai Express,Chennai
STORE005,ShelfSmart Hyderabad Plaza,Hyderabad
STORE006,ShelfSmart Pune Market,Pune
STORE007,ShelfSmart Ahmedabad Center,Ahmedabad
STORE008,ShelfSmart Kolkata Mall,Kolkata
STORE009,ShelfSmart Jaipur Outlet,Jaipur
STORE010,ShelfSmart Kochi Store,Kochi
```


---

### 2.4 Fact Table: `fact_sales.csv`

**Purpose:** Transactional sales data (core fact table)

**Schema:**
| Column Name | Data Type | Description | Constraints |
|-------------|-----------|-------------|-------------|
| transaction_id | VARCHAR(20) | Unique transaction identifier | PRIMARY KEY, NOT NULL |
| customer_id | VARCHAR(10) | Foreign key to dim_customers | FOREIGN KEY, NOT NULL |
| product_id | VARCHAR(10) | Foreign key to dim_products | FOREIGN KEY, NOT NULL |
| quantity | INTEGER | Number of units sold | NOT NULL, CHECK (quantity > 0) |
| unit_price | DECIMAL(10,2) | Price per unit at transaction | NOT NULL, CHECK (unit_price > 0) |
| store_id | VARCHAR(10) | Foreign key to dim_stores | FOREIGN KEY, NOT NULL |
| transaction_date | TIMESTAMP | Date and time of transaction | NOT NULL |

**Sample Data:**
```csv
transaction_id,customer_id,product_id,quantity,unit_price,store_id,transaction_date
TXN536365-1,CUST17850,PROD85123A,6,2.55,STORE001,2010-12-01 08:26:00
TXN536365-2,CUST17850,PROD71053,6,3.39,STORE001,2010-12-01 08:26:00
TXN536365-3,CUST17850,PROD84406B,8,2.75,STORE001,2010-12-01 08:26:00
TXN536366-1,CUST17850,PROD22633,6,1.85,STORE001,2010-12-01 08:28:00
TXN536367-1,CUST13047,PROD84879,32,1.69,STORE002,2010-12-01 08:34:00
TXN536380-1,CUST14527,PROD22960,12,4.25,STORE003,2010-12-01 09:41:00
TXN536381-1,CUST15311,PROD21730,12,1.25,STORE004,2010-12-01 09:41:00
TXN536382-1,CUST16250,PROD22423,1,12.75,STORE005,2010-12-01 09:45:00
TXN536383-1,CUST12583,PROD85099B,12,1.95,STORE006,2010-12-01 09:49:00
TXN536384-1,CUST13748,PROD22086,12,2.55,STORE007,2010-12-01 09:52:00
TXN536385-1,CUST14096,PROD84029E,6,3.75,STORE008,2010-12-01 10:03:00
TXN536386-1,CUST15769,PROD22111,6,4.95,STORE009,2010-12-01 10:05:00
TXN536387-1,CUST17677,PROD21034,4,4.15,STORE010,2010-12-01 10:08:00
TXN536388-1,CUST17850,PROD22616,12,0.85,STORE001,2010-12-01 10:10:00
TXN536389-1,CUST13047,PROD22492,48,0.65,STORE002,2010-12-01 10:15:00
```


---

### 2.5 Fact Table: `fact_inventory.csv`

**Purpose:** Current stock levels by store and product

**Schema:**
| Column Name | Data Type | Description | Constraints |
|-------------|-----------|-------------|-------------|
| store_id | VARCHAR(10) | Foreign key to dim_stores | FOREIGN KEY, NOT NULL |
| product_id | VARCHAR(10) | Foreign key to dim_products | FOREIGN KEY, NOT NULL |
| stock_on_hand | INTEGER | Current inventory quantity | NOT NULL, CHECK (stock_on_hand >= 0) |
| last_restock_date | DATE | Date of last restocking | NOT NULL |

**Composite Primary Key:** (store_id, product_id)

**Sample Data:**
```csv
store_id,product_id,stock_on_hand,last_restock_date
STORE001,PROD85123A,145,2024-01-10
STORE001,PROD71053,89,2024-01-12
STORE001,PROD84406B,203,2024-01-08
STORE001,PROD22633,67,2024-01-14
STORE001,PROD84879,312,2024-01-09
STORE002,PROD85123A,178,2024-01-11
STORE002,PROD71053,95,2024-01-13
STORE002,PROD84406B,156,2024-01-10
STORE002,PROD22633,88,2024-01-15
STORE002,PROD84879,267,2024-01-08
STORE003,PROD22960,124,2024-01-09
STORE003,PROD21730,234,2024-01-12
STORE003,PROD22423,45,2024-01-14
STORE003,PROD85099B,189,2024-01-10
STORE004,PROD22086,156,2024-01-11
```


---

### 2.6 Fact Table: `fact_shipments.csv`

**Purpose:** Delivery and shipment tracking information

**Schema:**
| Column Name | Data Type | Description | Constraints |
|-------------|-----------|-------------|-------------|
| shipment_id | VARCHAR(20) | Unique shipment identifier | PRIMARY KEY, NOT NULL |
| transaction_id | VARCHAR(20) | Foreign key to fact_sales | FOREIGN KEY, NOT NULL |
| status | VARCHAR(50) | Shipment status | NOT NULL |
| delivery_time_days | INTEGER | Days taken for delivery | NOT NULL, CHECK (delivery_time_days >= 0) |
| shipment_date | DATE | Date shipment was dispatched | NOT NULL |

**Sample Data:**
```csv
shipment_id,transaction_id,status,delivery_time_days,shipment_date
SHIP536365-1,TXN536365-1,Delivered,3,2010-12-01
SHIP536365-2,TXN536365-2,Delivered,3,2010-12-01
SHIP536365-3,TXN536365-3,Delivered,3,2010-12-01
SHIP536366-1,TXN536366-1,Delivered,5,2010-12-01
SHIP536367-1,TXN536367-1,Delivered,4,2010-12-01
SHIP536380-1,TXN536380-1,Delivered,7,2010-12-01
SHIP536381-1,TXN536381-1,Delivered,6,2010-12-01
SHIP536382-1,TXN536382-1,Delivered,8,2010-12-01
SHIP536383-1,TXN536383-1,Delivered,5,2010-12-01
SHIP536384-1,TXN536384-1,Delivered,9,2010-12-01
SHIP536385-1,TXN536385-1,In Transit,0,2010-12-01
SHIP536386-1,TXN536386-1,Delivered,4,2010-12-01
SHIP536387-1,TXN536387-1,Delivered,6,2010-12-01
SHIP536388-1,TXN536388-1,Delivered,5,2010-12-01
SHIP536389-1,TXN536389-1,Delivered,7,2010-12-01
```

**Status Values:**
- `Delivered`: Successfully delivered to customer
- `In Transit`: Currently being shipped
- `Processing`: Being prepared for shipment
- `Delayed`: Experiencing delivery delays

---

## 3. DATA QUALITY RULES APPLIED

### 3.1 General Cleaning Rules
✅ **Remove Nulls:** All primary/foreign keys must be NOT NULL
✅ **Remove Duplicates:** Deduplicate based on primary keys
✅ **Standardize Formats:** Consistent date/time formats, text casing
✅ **Validate Ranges:** Prices > 0, quantities > 0, dates within valid range
✅ **Referential Integrity:** All foreign keys must exist in referenced tables

### 3.2 Specific Transformations

**For fact_sales:**
- Excluded transactions with InvoiceNo starting with 'C' (cancellations)
- Excluded negative quantities (returns)
- Excluded missing CustomerID
- Excluded zero/negative prices
- Created unique transaction_id for line-item level granularity

**For dim_products:**
- Removed products with no description
- Standardized description text (title case, trim)
- Categorized products based on keyword matching
- Assigned suppliers based on category

**For dim_customers:**
- Generated synthetic names (original data didn't have)
- Mapped countries to Indian cities
- Created email from name pattern
- Added metadata timestamp

### 3.3 Data Validation Checks

**Record Counts:**
```sql
-- Validate no orphan records
SELECT COUNT(*) FROM fact_sales fs
LEFT JOIN dim_customers dc ON fs.customer_id = dc.customer_id
WHERE dc.customer_id IS NULL;
-- Expected: 0

SELECT COUNT(*) FROM fact_sales fs
LEFT JOIN dim_products dp ON fs.product_id = dp.product_id
WHERE dp.product_id IS NULL;
-- Expected: 0

-- Validate positive values
SELECT COUNT(*) FROM fact_sales WHERE quantity <= 0 OR unit_price <= 0;
-- Expected: 0

-- Validate date ranges
SELECT MIN(transaction_date), MAX(transaction_date) FROM fact_sales;
-- Expected: Within 2010-2011 range
```

---

## 4. DATABASE SCHEMA DIAGRAM

```
┌─────────────────────┐
│  dim_customers      │
├─────────────────────┤
│ PK customer_id      │
│    name             │
│    email            │
│    city             │
│    update_timestamp │
└─────────────────────┘
          │
          │ 1:N
          ▼
┌─────────────────────┐      ┌─────────────────────┐
│  fact_sales         │  N:1 │  dim_products       │
├─────────────────────┤◄─────├─────────────────────┤
│ PK transaction_id   │      │ PK product_id       │
│ FK customer_id      │      │    description      │
│ FK product_id       │      │    base_price       │
│ FK store_id         │      │    category         │
│    quantity         │      │    supplier_id      │
│    unit_price       │      └─────────────────────┘
│    transaction_date │
└─────────────────────┘
          │                  ┌─────────────────────┐
          │ 1:1              │  dim_stores         │
          ▼                  ├─────────────────────┤
┌─────────────────────┐      │ PK store_id         │
│  fact_shipments     │  N:1 │    store_name       │
├─────────────────────┤◄─────│    city             │
│ PK shipment_id      │      └─────────────────────┘
│ FK transaction_id   │               │
│    status           │               │ 1:N
│    delivery_time_   │               ▼
│    shipment_date    │      ┌─────────────────────┐
└─────────────────────┘      │  fact_inventory     │
                             ├─────────────────────┤
                             │ PK store_id         │
                             │ PK product_id       │
                             │    stock_on_hand    │
                             │    last_restock_    │
                             └─────────────────────┘
```

---

## 5. SAMPLE QUERIES TO VALIDATE DATA

### 5.1 Data Quality Checks
```sql
-- Check for orphaned foreign keys
SELECT 'Orphaned Customers' as check_type, COUNT(*) as count
FROM fact_sales fs
LEFT JOIN dim_customers dc ON fs.customer_id = dc.customer_id
WHERE dc.customer_id IS NULL

UNION ALL

SELECT 'Orphaned Products', COUNT(*)
FROM fact_sales fs
LEFT JOIN dim_products dp ON fs.product_id = dp.product_id
WHERE dp.product_id IS NULL

UNION ALL

SELECT 'Orphaned Stores', COUNT(*)
FROM fact_sales fs
LEFT JOIN dim_stores ds ON fs.store_id = ds.store_id
WHERE ds.store_id IS NULL;
```

### 5.2 Business Validation
```sql
-- Validate revenue calculations
SELECT 
    COUNT(*) as total_transactions,
    SUM(quantity * unit_price) as total_revenue,
    AVG(quantity * unit_price) as avg_transaction_value,
    MIN(transaction_date) as earliest_sale,
    MAX(transaction_date) as latest_sale
FROM fact_sales;

-- Check product distribution
SELECT 
    category,
    COUNT(DISTINCT product_id) as product_count,
    AVG(base_price) as avg_price
FROM dim_products
GROUP BY category
ORDER BY product_count DESC;

-- Validate inventory levels
SELECT 
    store_id,
    COUNT(DISTINCT product_id) as products_stocked,
    SUM(stock_on_hand) as total_inventory,
    AVG(stock_on_hand) as avg_stock_per_product
FROM fact_inventory
GROUP BY store_id;
```

---

## 6. DATA STATISTICS

### Original Dataset (online_retail.csv)
- **Total Records:** ~541,909 rows
- **Date Range:** Dec 2010 - Dec 2011
- **Unique Customers:** ~4,372
- **Unique Products:** ~3,684
- **Countries:** 38

### Cleaned Dataset Summary
| Table | Records (Approx) | Unique Keys |
|-------|------------------|-------------|
| dim_customers | 4,372 | customer_id |
| dim_products | 3,684 | product_id |
| dim_stores | 10 | store_id |
| fact_sales | 400,000+ | transaction_id |
| fact_inventory | 36,840 | (store_id, product_id) |
| fact_shipments | 400,000+ | shipment_id |

### Data Reduction
- **Removed:** ~26% of raw records due to:
  - Cancelled transactions (C prefix invoices)
  - Missing CustomerIDs
  - Negative quantities (returns)
  - Invalid prices (≤ 0)
  - Duplicate records

---

## 7. FILES READY FOR DATABASE INGESTION

All tables are stored as CSV files with:
✅ **Clean headers** (no special characters)
✅ **Consistent delimiters** (comma-separated)
✅ **UTF-8 encoding**
✅ **Proper NULL handling** (empty strings for NULLs)
✅ **Date format:** YYYY-MM-DD or YYYY-MM-DD HH:MM:SS
✅ **No trailing spaces**

**File List:**
```
1. dim_customers.csv
2. dim_products.csv
3. dim_stores.csv
4. fact_sales.csv
5. fact_inventory.csv
6. fact_shipments.csv
```

**Load Order (to maintain referential integrity):**
```
1. Load dimensions first:
   - dim_customers
   - dim_products
   - dim_stores

2. Load facts second:
   - fact_sales (depends on all dimensions)
   - fact_inventory (depends on dim_stores, dim_products)
   - fact_shipments (depends on fact_sales)
```

---

## 8. NEXT STEPS FOR DATABASE INGESTION

### 8.1 Create Tables (DuckDB/PostgreSQL)
```sql
-- Create dimension tables
CREATE TABLE dim_customers (
    customer_id VARCHAR(10) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE,
    city VARCHAR(100) NOT NULL,
    update_timestamp TIMESTAMP NOT NULL
);

CREATE TABLE dim_products (
    product_id VARCHAR(10) PRIMARY KEY,
    description VARCHAR(500) NOT NULL,
    base_price DECIMAL(10,2) NOT NULL CHECK (base_price > 0),
    category VARCHAR(100) NOT NULL,
    supplier_id VARCHAR(10) NOT NULL
);

CREATE TABLE dim_stores (
    store_id VARCHAR(10) PRIMARY KEY,
    store_name VARCHAR(100) NOT NULL,
    city VARCHAR(100) NOT NULL
);

-- Create fact tables
CREATE TABLE fact_sales (
    transaction_id VARCHAR(20) PRIMARY KEY,
    customer_id VARCHAR(10) NOT NULL,
    product_id VARCHAR(10) NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(10,2) NOT NULL CHECK (unit_price > 0),
    store_id VARCHAR(10) NOT NULL,
    transaction_date TIMESTAMP NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES dim_customers(customer_id),
    FOREIGN KEY (product_id) REFERENCES dim_products(product_id),
    FOREIGN KEY (store_id) REFERENCES dim_stores(store_id)
);

CREATE TABLE fact_inventory (
    store_id VARCHAR(10),
    product_id VARCHAR(10),
    stock_on_hand INTEGER NOT NULL CHECK (stock_on_hand >= 0),
    last_restock_date DATE NOT NULL,
    PRIMARY KEY (store_id, product_id),
    FOREIGN KEY (store_id) REFERENCES dim_stores(store_id),
    FOREIGN KEY (product_id) REFERENCES dim_products(product_id)
);

CREATE TABLE fact_shipments (
    shipment_id VARCHAR(20) PRIMARY KEY,
    transaction_id VARCHAR(20) NOT NULL,
    status VARCHAR(50) NOT NULL,
    delivery_time_days INTEGER NOT NULL CHECK (delivery_time_days >= 0),
    shipment_date DATE NOT NULL,
    FOREIGN KEY (transaction_id) REFERENCES fact_sales(transaction_id)
);
```

### 8.2 Load Data
```sql
-- DuckDB example
COPY dim_customers FROM 'dim_customers.csv' (HEADER TRUE);
COPY dim_products FROM 'dim_products.csv' (HEADER TRUE);
COPY dim_stores FROM 'dim_stores.csv' (HEADER TRUE);
COPY fact_sales FROM 'fact_sales.csv' (HEADER TRUE);
COPY fact_inventory FROM 'fact_inventory.csv' (HEADER TRUE);
COPY fact_shipments FROM 'fact_shipments.csv' (HEADER TRUE);
```

---

## 9. CONTACT & MAINTENANCE

**Data Owner:** ShelfSmart Analytics Team
**Last Updated:** 2024-01-15
**Refresh Frequency:** Daily (for fact tables), Weekly (for dimension tables)
**Data Quality SLA:** 99.5% accuracy, validated daily

**For questions or issues, contact:** analytics@shelfsmart.coms