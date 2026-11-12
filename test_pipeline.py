import pandas as pd
import pytest
from src.pipeline import prepare_model_table, validate_model_table

def fixture():
    return pd.DataFrame({
        "Delivery Status": ["Late delivery", "Shipping on time", "Shipping canceled"],
        "Late_delivery_risk": [1, 0, 0],
        "Days for shipping (real)": [5, 2, 6],
        "Days for shipment (scheduled)": [4, 2, 4],
        "shipping date (DateOrders)": ["1/5/2018 00:00"]*3,
        "order date (DateOrders)": ["1/1/2018 00:00"]*3,
        "Customer Email": ["x", "y", "z"], "Order Item Id": [1,2,3],
        "Shipping Mode": ["Standard", "First", "Second"], "Sales": [100,200,300],
    })

def test_excludes_cancelled_and_leakage():
    out = prepare_model_table(fixture())
    assert len(out) == 2
    assert out["late_delivery"].tolist() == [1,0]
    assert "Delivery Status" not in out and "Late_delivery_risk" not in out
    assert "Customer Email" not in out

def test_validation_passes():
    out = prepare_model_table(fixture())
    assert validate_model_table(out, minimum_rows=2)["success"] is True

def test_invalid_label_disagreement_fails():
    bad = fixture(); bad.loc[0, "Late_delivery_risk"] = 0
    with pytest.raises(ValueError):
        prepare_model_table(bad)
