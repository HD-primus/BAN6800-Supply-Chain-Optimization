"""FastAPI inference service for the BAN6800 late-delivery model."""
from pathlib import Path
from datetime import datetime
import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

ROOT=Path(__file__).resolve().parents[1]
BUNDLE=joblib.load(ROOT/'models'/'model_bundle.joblib')
app=FastAPI(title='BAN6800 Late Delivery Risk API',version='1.0.0')

class OrderFeatures(BaseModel):
    order_datetime: str = Field(..., description='Order timestamp, ISO 8601 format')
    Type: str
    Days_for_shipment_scheduled: int = Field(...,ge=0)
    Order_Item_Discount_Rate: float = Field(...,ge=0)
    Product_Price: float = Field(...,ge=0)
    Order_Item_Quantity: int = Field(...,ge=1)
    Category_Name: str
    Customer_Segment: str
    Department_Name: str
    Market: str
    Order_Region: str
    Product_Name: str
    Shipping_Mode: str

@app.get('/health')
def health():
    return {'status':'ok','model_version':BUNDLE['model_version']}

@app.post('/predict')
def predict(order: OrderFeatures):
    try:
        dt=pd.to_datetime(order.order_datetime,errors='raise')
        row={
          'Days for shipment (scheduled)':order.Days_for_shipment_scheduled,
          'Order Item Discount Rate':order.Order_Item_Discount_Rate,
          'Product Price':order.Product_Price,
          'Order Item Quantity':order.Order_Item_Quantity,
          'order_month':dt.month,'order_dayofweek':dt.dayofweek,'order_hour':dt.hour,
          'order_day':dt.day,'order_year':dt.year,'order_quarter':dt.quarter,
          'Type':order.Type,'Category Name':order.Category_Name,'Customer Segment':order.Customer_Segment,
          'Department Name':order.Department_Name,'Market':order.Market,'Order Region':order.Order_Region,
          'Product Name':order.Product_Name,'Shipping Mode':order.Shipping_Mode
        }
        X=pd.DataFrame([row],columns=BUNDLE['features'])
        Xp=BUNDLE['preprocessor'].transform(X)
        probability=float(BUNDLE['model'].predict_proba(Xp)[0,1])
        threshold=float(BUNDLE['threshold'])
        return {'model_version':BUNDLE['model_version'],'late_delivery_probability':round(probability,6),
                'high_risk_flag':bool(probability>=threshold),'decision_threshold':threshold,
                'interpretation':'Risk estimate for decision support; human review is required.'}
    except Exception as exc:
        raise HTTPException(status_code=400,detail=f'Invalid input: {exc}')
