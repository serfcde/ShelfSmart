import pandas as pd
import polars as pl
from mlxtend.frequent_patterns import apriori, association_rules
import os

def run_market_basket_analysis(min_support=0.03, min_threshold=1.2):
    # 1. SETUP PATHS - Align with your folder structure
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(base_dir, "../../data/data_hub/fact_sales.parquet")
    output_path = os.path.join(base_dir, "../../data/data_hub/market_basket_rules.parquet")
    
    # 2. LOAD DATA (Using Polars for speed)
    df = pl.read_parquet(input_path)
    
    # 3. FILTERING (Optional but Recommended)
    # Removing very rare items prevents the "Memory Error" in the Apriori algorithm
    top_items = df.group_by("Description").len().filter(pl.col("len") > 15)["Description"]
    df_filtered = df.filter(pl.col("Description").is_in(top_items))
    
    # 4. TRANSFORMATION (Pivot is more efficient than TransactionEncoder for this size)
    # Using 'InvoiceNo' as transaction_id and 'Description' as product_name
    basket = (df_filtered.pivot(
        values="Quantity", 
        index="InvoiceNo", 
        on="Description", 
        aggregate_function="sum"
    ).fill_null(0))
    
    # 5. ENCODING
    # Convert to True/False (Boolean) which mlxtend prefers
    basket_df = basket.drop("InvoiceNo").to_pandas()
    basket_bool = basket_df.astype(bool)
    
    # 6. ALGORITHM: Find Frequent Itemsets
    frequent_itemsets = apriori(basket_bool, min_support=min_support, use_colnames=True)
    
    if frequent_itemsets.empty:
        print("⚠️ No frequent itemsets found. Try lowering min_support.")
        return pd.DataFrame()

    # 7. RULES: Generate Association Rules
    rules = association_rules(frequent_itemsets, metric="lift", min_threshold=min_threshold)
    
    # 8. CLEAN UP FOR POWER BI
    # Power BI cannot read 'frozensets', so we must convert them to strings
    rules = rules[['antecedents', 'consequents', 'support', 'confidence', 'lift']]
    rules['antecedents'] = rules['antecedents'].apply(lambda x: ', '.join(list(x)))
    rules['consequents'] = rules['consequents'].apply(lambda x: ', '.join(list(x)))
    
    # 9. SAVE TO DATA_HUB
    rules_pl = pl.from_pandas(rules)
    rules_pl.write_parquet(output_path)
    print(f"✅ Market Basket Rules exported to: {output_path}")
    
    return rules