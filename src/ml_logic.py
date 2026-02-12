import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder

def run_market_basket_analysis(df, min_support=0.02, min_threshold=1.0):
    """
    Computes Association Rules from transaction data.
    Input df should have columns: ['transaction_id', 'product_name']
    """
    # 1. Transform
    basket = df.groupby('transaction_id')['product_name'].apply(list).tolist()
    
    # 2. Encoding
    te = TransactionEncoder()
    te_ary = te.fit(basket).transform(basket)
    transformed_df = pd.DataFrame(te_ary, columns=te.columns_)
    
    # 3. Algorithm: Find Frequent Itemsets
    frequent_itemsets = apriori(transformed_df, min_support=min_support, use_colnames=True)
    
    if frequent_itemsets.empty:
        return pd.DataFrame()

    # 4. Rules: Generate Association Rules (Lift, Confidence)
    rules = association_rules(frequent_itemsets, metric="lift", min_threshold=min_threshold)
    
    # Clean up results for the dashboard
    rules = rules[['antecedents', 'consequents', 'support', 'confidence', 'lift']]
    rules['antecedents'] = rules['antecedents'].apply(lambda x: ', '.join(list(x)))
    rules['consequents'] = rules['consequents'].apply(lambda x: ', '.join(list(x)))
    
    return rules.sort_values('lift', ascending=False)

