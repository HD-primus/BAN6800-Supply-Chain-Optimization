"""Optional Great Expectations 0.18.x validation runner (not executed here)."""
import pandas as pd
import great_expectations as ge
import sys

path = sys.argv[1] if len(sys.argv) > 1 else "data/processed/model_ready.csv.gz"
df = pd.read_csv(path, compression="gzip" if path.endswith(".gz") else None)
gdf = ge.from_pandas(df)
gdf.expect_table_row_count_to_be_between(min_value=5000)
gdf.expect_column_to_exist("late_delivery")
gdf.expect_column_values_to_not_be_null("late_delivery")
gdf.expect_column_values_to_be_in_set("late_delivery", [0, 1])
gdf.expect_column_values_to_be_unique("late_delivery") if False else None
for forbidden in ["Delivery Status", "Late_delivery_risk", "Customer Email", "Customer Password", "Days for shipping (real)"]:
    if forbidden in df.columns:
        raise AssertionError(f"Forbidden field remains: {forbidden}")
result = gdf.validate()
print(result)
if not result["success"]:
    raise SystemExit(1)
