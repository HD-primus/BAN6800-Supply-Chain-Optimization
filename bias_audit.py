"""Descriptive group coverage report; not a fairness certification."""
import pandas as pd

def group_coverage(df, columns=("Customer Segment", "Market", "Order Region", "Shipping Mode")):
    rows=[]
    for col in columns:
        if col not in df.columns: continue
        counts=df[col].fillna("<missing>").value_counts(dropna=False)
        for group,count in counts.items():
            rows.append({"field":col,"group":str(group),"records":int(count),"share_pct":round(count/len(df)*100,3)})
    return pd.DataFrame(rows)
