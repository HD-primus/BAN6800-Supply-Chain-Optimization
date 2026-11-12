"""Reproducible DataCo pipeline for BAN6800 Module 3.

The script intentionally excludes customer direct identifiers, label fields and
post-outcome variables before publishing the model-ready feature table.
"""
from pathlib import Path
import argparse, hashlib, json
import pandas as pd

DIRECT_IDENTIFIERS = [
    "Customer Email", "Customer Fname", "Customer Lname", "Customer Password",
    "Customer Street", "Customer Id", "Order Customer Id", "Customer Zipcode",
    "Customer City", "Customer State", "Latitude", "Longitude", "Order Zipcode",
    "Order Id", "Order Item Id", "Product Image", "Product Description",
]
POST_OUTCOME_FIELDS = [
    "Delivery Status", "Late_delivery_risk", "Days for shipping (real)",
    "shipping date (DateOrders)", "Order Status",
]
DATE_COLUMNS = ["order date (DateOrders)", "shipping date (DateOrders)"]
NUMERIC_COLUMNS = [
    "Days for shipping (real)", "Days for shipment (scheduled)", "Benefit per order",
    "Sales per customer", "Late_delivery_risk", "Category Id", "Customer Id",
    "Customer Zipcode", "Department Id", "Latitude", "Longitude", "Order Customer Id",
    "Order Id", "Order Item Cardprod Id", "Order Item Discount",
    "Order Item Discount Rate", "Order Item Id", "Order Item Product Price",
    "Order Item Profit Ratio", "Order Item Quantity", "Sales", "Order Item Total",
    "Order Profit Per Order", "Order Zipcode", "Product Card Id", "Product Category Id",
    "Product Price", "Product Status",
]

def load_raw(path):
    return pd.read_csv(path, encoding="latin-1", low_memory=False)

def prepare_model_table(raw):
    df = raw.copy()
    df.columns = [str(c).strip() for c in df.columns]
    df = df.drop_duplicates().copy()
    for c in df.select_dtypes(include="object").columns:
        df[c] = df[c].map(lambda v: v.strip() if isinstance(v, str) else v)
        df[c] = df[c].replace({"": pd.NA})
    for c in DATE_COLUMNS:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], format="%m/%d/%Y %H:%M", errors="coerce")
    for c in NUMERIC_COLUMNS:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    required = {"Delivery Status", "Late_delivery_risk"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Required target columns missing: {sorted(missing)}")

    # Cancellation is not a completed delivery outcome and is excluded from this classifier.
    df = df.loc[~df["Delivery Status"].eq("Shipping canceled")].copy()
    y = pd.to_numeric(df["Late_delivery_risk"], errors="coerce")
    if y.isna().any() or not y.isin([0, 1]).all():
        raise ValueError("Late_delivery_risk must be complete and binary for retained records.")
    status_y = df["Delivery Status"].eq("Late delivery").astype("int8")
    if not y.astype("int8").reset_index(drop=True).equals(status_y.reset_index(drop=True)):
        raise ValueError("Late_delivery_risk disagrees with Delivery Status on retained records.")
    df["late_delivery"] = y.astype("int8")

    # Keep broad order-time/product/market features; remove direct identifiers,
    # delivery outcome labels, and fields only known after the shipment outcome.
    drop = [c for c in DIRECT_IDENTIFIERS + POST_OUTCOME_FIELDS if c in df.columns]
    out = df.drop(columns=drop)
    out = out.drop(columns=[c for c in out.columns if out[c].isna().all()])
    out = out.dropna(axis=0, how="any")
    out = out[["late_delivery"] + [c for c in out.columns if c != "late_delivery"]]
    return out

def validate_model_table(df, minimum_rows=5000):
    checks = {
        "minimum_rows_5000": bool(len(df) >= minimum_rows),
        "target_present": bool("late_delivery" in df.columns),
        "target_non_null": bool("late_delivery" in df.columns and df["late_delivery"].notna().all()),
        "target_binary": bool("late_delivery" in df.columns and df["late_delivery"].isin([0, 1]).all()),
        "unique_column_names": bool(df.columns.is_unique),
        "no_direct_identifiers": bool(not any(c in df.columns for c in DIRECT_IDENTIFIERS)),
        "no_post_outcome_fields": bool(not any(c in df.columns for c in POST_OUTCOME_FIELDS)),
        "no_missing_values": bool(not df.isna().any().any()),
    }
    if not all(checks.values()):
        raise ValueError(f"Data validation failed: {checks}")
    return {"success": True, "row_count": int(len(df)), "column_count": int(len(df.columns)),
            "target_counts": {str(k): int(v) for k, v in df["late_delivery"].value_counts().items()},
            "checks": checks}

def profile_source(raw, source_path):
    return {
        "file": Path(source_path).name,
        "encoding_used": "latin-1",
        "rows": int(raw.shape[0]), "columns": int(raw.shape[1]),
        "exact_duplicate_rows": int(raw.duplicated().sum()),
        "unique_order_item_ids": int(raw["Order Item Id"].nunique()),
        "duplicate_order_item_ids": int(raw["Order Item Id"].duplicated().sum()),
        "missing_cells_total": int(raw.isna().sum().sum()),
        "missing_by_column": {c: {"count": int(n), "percentage": round(float(n/len(raw)*100), 3)}
                               for c,n in raw.isna().sum().items() if n},
        "date_parse": {c: {"valid": int(pd.to_datetime(raw[c], format="%m/%d/%Y %H:%M", errors="coerce").notna().sum()),
                            "invalid": int(pd.to_datetime(raw[c], format="%m/%d/%Y %H:%M", errors="coerce").isna().sum())}
                        for c in DATE_COLUMNS if c in raw.columns},
        "delivery_status_counts": {str(k): int(v) for k,v in raw["Delivery Status"].value_counts(dropna=False).items()},
        "late_delivery_risk_counts": {str(k): int(v) for k,v in raw["Late_delivery_risk"].value_counts(dropna=False).items()},
        "late_risk_matches_status": bool((raw["Late_delivery_risk"].astype(int).reset_index(drop=True) == raw["Delivery Status"].eq("Late delivery").astype(int).reset_index(drop=True)).all()),
    }

def run(input_path, output_path, report_dir):
    raw = load_raw(input_path)
    source_profile = profile_source(raw, input_path)
    model = prepare_model_table(raw)
    validation = validate_model_table(model)
    output_path = Path(output_path); output_path.parent.mkdir(parents=True, exist_ok=True)
    model.to_csv(output_path, index=False, compression="gzip" if str(output_path).endswith(".gz") else None)
    output_hash = hashlib.sha256(output_path.read_bytes()).hexdigest()
    report_dir = Path(report_dir); report_dir.mkdir(parents=True, exist_ok=True)
    source_profile.update({
        "cancelled_order_items_excluded": int((raw["Delivery Status"] == "Shipping canceled").sum()),
        "risk_vs_actual_days_mismatch_rows": int(((raw["Days for shipping (real)"] > raw["Days for shipment (scheduled)"]) != (raw["Late_delivery_risk"] == 1)).sum()),
        "model_ready_rows": int(len(model)), "model_ready_columns_including_target": int(len(model.columns)),
        "model_ready_feature_columns": int(len(model.columns)-1),
        "model_ready_target_counts": validation["target_counts"],
        "model_ready_excluded_columns": [c for c in raw.columns if c not in model.columns],
        "output_sha256": output_hash,
        "interpretation": "The supplied Late_delivery_risk label is used for non-cancelled records and cross-checked against Delivery Status. The actual-days comparison is not used as the label because it flags cancelled rows.",
    })
    validation.update({"output_file": str(output_path), "output_sha256": output_hash,
                       "great_expectations_executed": False,
                       "validation_note": "Local pandas assertions and pytest are executed; Great Expectations requires separate installation and execution."})
    (report_dir / "data_quality_profile.json").write_text(json.dumps(source_profile, indent=2), encoding="utf-8")
    (report_dir / "pipeline_validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    raw.isna().sum().rename("missing_count").to_csv(report_dir / "missingness_report.csv")
    return validation, source_profile

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--output", default="data/processed/model_ready.csv.gz")
    p.add_argument("--reports", default="reports")
    args = p.parse_args()
    result, _ = run(args.input, args.output, args.reports)
    print(json.dumps(result, indent=2))
