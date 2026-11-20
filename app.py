from pathlib import Path
from datetime import datetime
import json
import joblib
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

ROOT = Path(__file__).resolve().parent
BUNDLE_PATH = ROOT / "models" / "model_bundle.joblib"
REPORTS = ROOT / "reports"

st.set_page_config(page_title="BAN6800 Supply Chain Risk Dashboard", page_icon="📦", layout="wide")
st.title("Supply Chain Late-Delivery Risk | Model Insights")
st.caption("BAN6800 Module 5 • DataCo public proxy dataset • Academic proof of concept, not Shell internal data")

@st.cache_resource
def load_bundle():
    return joblib.load(BUNDLE_PATH)

@st.cache_data
def load_json(name):
    return json.loads((REPORTS / name).read_text())

@st.cache_data
def load_csv(name):
    return pd.read_csv(REPORTS / name)

bundle = load_bundle()
metrics_doc = load_json("model_validation_metrics.json")
runout = load_json("run_output.json")
test = metrics_doc["test_metrics"]
fair = load_csv("fairness_summary.csv")
shap_global = load_csv("shap_global_importance.csv")
shap_local = load_csv("shap_local_explanation.csv")
ablation = load_csv("feature_ablation.csv")
comparison = load_csv("model_comparison_validation.csv")

pages = ["Overview", "Prediction explorer", "Explainability", "Operational fairness", "Limitations & governance"]
page = st.sidebar.radio("Dashboard section", pages)

if page == "Overview":
    st.subheader("Final test performance")
    cols = st.columns(4)
    for c, (label, value) in zip(cols, [
        ("Recall", f"{test['recall']:.1%}"),
        ("Precision", f"{test['precision']:.1%}"),
        ("ROC-AUC", f"{test['roc_auc']:.3f}"),
        ("PR-AUC", f"{test['pr_auc']:.3f}")
    ]):
        c.metric(label, value)
    st.caption(f"Threshold: {test['decision_threshold']:.2f} • Test records: {test['n_test']:,} • Test late rate: {test['test_late_rate']:.2%}")
    left, right = st.columns(2)
    with left:
        cm = metrics_doc["confusion_matrix"]
        cm_df = pd.DataFrame(cm, index=["Actual on-time", "Actual late"], columns=["Predicted not flagged", "Predicted flagged"])
        st.write("**Confusion matrix (counts)**")
        st.dataframe(cm_df, use_container_width=True)
    with right:
        st.write("**Validation model comparison (ROC-AUC)**")
        fig = px.bar(comparison, x="model", y="roc_auc", range_y=[0,1], text_auto=".3f")
        st.plotly_chart(fig, use_container_width=True)
    st.info("These are historical test results on DataCo records. They do not measure reductions in real operational delivery delays or inventory costs.")

elif page == "Prediction explorer":
    st.subheader("What-if prediction explorer")
    st.write("Enter order-time information. The dashboard applies the saved preprocessing pipeline and XGBoost model.")
    with st.form("predict_form"):
        c1,c2,c3 = st.columns(3)
        with c1:
            order_date = st.date_input("Order date", value=datetime(2018,1,31).date())
            order_time = st.time_input("Order time", value=datetime.strptime("14:30","%H:%M").time())
            ship_days = st.number_input("Scheduled shipping days", min_value=0, max_value=30, value=3)
            shipping = st.selectbox("Shipping mode", ["Standard Class","Second Class","First Class","Same Day"])
            transaction = st.selectbox("Transaction type", ["DEBIT","TRANSFER","CASH","PAYMENT"])
        with c2:
            market = st.selectbox("Market", ["LATAM","Europe","Pacific Asia","USCA","Africa","Asia Pacific"])
            region = st.selectbox("Order region", ["Central America","Western Europe","Southeast Asia","Caribbean","West Africa","East Africa","Northern Europe","South America"])
            segment = st.selectbox("Customer segment", ["Consumer","Corporate","Home Office"])
            category = st.text_input("Category name", "Sporting Goods")
            department = st.text_input("Department name", "Fitness")
        with c3:
            product = st.text_input("Product name", "Smart watch")
            price = st.number_input("Product price", min_value=0.0, value=327.75, step=1.0)
            quantity = st.number_input("Order item quantity", min_value=1, value=1, step=1)
            discount = st.number_input("Discount rate", min_value=0.0, max_value=1.0, value=0.04, step=0.01)
        submitted = st.form_submit_button("Score this scenario", type="primary")
    if submitted:
        dt = datetime.combine(order_date, order_time)
        row = {
            "Days for shipment (scheduled)": int(ship_days),
            "Order Item Discount Rate": float(discount),
            "Product Price": float(price),
            "Order Item Quantity": int(quantity),
            "order_month": dt.month, "order_dayofweek": dt.weekday(), "order_hour": dt.hour,
            "order_day": dt.day, "order_year": dt.year, "order_quarter": (dt.month-1)//3+1,
            "Type": transaction, "Category Name": category, "Customer Segment": segment,
            "Department Name": department, "Market": market, "Order Region": region,
            "Product Name": product, "Shipping Mode": shipping
        }
        try:
            X = pd.DataFrame([row], columns=bundle["features"])
            Xp = bundle["preprocessor"].transform(X)
            probability = float(bundle["model"].predict_proba(Xp)[0,1])
            threshold = float(bundle["threshold"])
            flagged = probability >= threshold
            st.metric("Predicted late-delivery probability", f"{probability:.1%}")
            if flagged:
                st.warning(f"High-risk flag at threshold {threshold:.2f}. Planner review is required.")
            else:
                st.success(f"Below the high-risk threshold of {threshold:.2f}. This is not a guarantee of on-time delivery.")
            st.caption("This is a model-based estimate, not a causal estimate. It must not trigger an automated adverse action.")
        except Exception as e:
            st.error(f"Could not score this combination: {e}")
            st.caption("Some typed categories may not have appeared in the training data. Try a common category or inspect the app logs.")

elif page == "Explainability":
    st.subheader("Global feature influence")
    top = runout["top_shap"][:10]
    df = pd.DataFrame(top)
    df["feature"] = df["feature"].str.replace("cat__","",regex=False).str.replace("num__","",regex=False)
    fig = px.bar(df.sort_values("mean_abs_shap"), x="mean_abs_shap", y="feature", orientation="h",
                 labels={"mean_abs_shap":"Mean absolute SHAP value","feature":"Feature"})
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Global SHAP values were calculated on a 600-row sample of the final test set. They describe model influence, not causation.")
    st.subheader("Saved local example")
    case = load_json("shap_local_case.json")
    a,b,c = st.columns(3)
    a.metric("Predicted late probability", f"{case['predicted_late_probability']:.2%}")
    b.metric("Decision threshold", f"{case['threshold']:.2f}")
    c.metric("Observed label", "Late" if case["actual_late"] == 1 else "Not late")
    st.json(case["input_context"])
    st.dataframe(shap_local.head(8), use_container_width=True)

elif page == "Operational fairness":
    st.subheader("Operational-group diagnostics")
    st.warning("The dataset has no verified demographic protected attributes. These are operational group comparisons, not demographic fairness findings or proof of discrimination.")
    fig = px.bar(fair, x="group_dimension", y="disparate_impact_ratio_min_over_max",
                 range_y=[0,1.05], text_auto=".3f",
                 labels={"group_dimension":"Operational dimension","disparate_impact_ratio_min_over_max":"Min/max high-risk flag-rate ratio"})
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(fair, use_container_width=True)
    st.write("TPR and FPR gaps are max-minus-min differences within each operational dimension.")
    st.caption("Group sizes, different observed late rates and missing categories in the later test window affect interpretation.")

elif page == "Limitations & governance":
    st.subheader("Model limitations")
    st.markdown("""
- DataCo is a public proxy dataset, not Shell internal operational data.
- The model is an academic proof of concept and is not approved for production.
- Recall is relatively high, but precision implies a material false-alert workload.
- SHAP describes model behaviour, not causality.
- Demographic fairness could not be assessed because verified protected attributes are absent.
- Strong dependence on scheduled-days and shipping-mode fields requires independent validation.
- Human review is required before any operational action.
""")
    st.subheader("Feature-ablation sensitivity")
    fig = px.bar(ablation, x="scenario", y="roc_auc", range_y=[0,0.9],
                 labels={"scenario":"Scenario","roc_auc":"Test ROC-AUC"})
    st.plotly_chart(fig, use_container_width=True)
    st.subheader("Transparency statement")
    st.markdown("Predictions are estimates for decision support only. Do not use this prototype to impose penalties, deny service, or automatically rank customers for exclusion.")
    with st.expander("Model card"):
        st.markdown((REPORTS/"model_card.md").read_text())
    with st.expander("Fairness methodology"):
        st.markdown((REPORTS/"fairness_metrics_report.md").read_text())

st.sidebar.markdown("---")
st.sidebar.caption("Model version: " + str(bundle.get("model_version","BAN6800-XGB-1.0")))
st.sidebar.caption("Threshold: 0.40 • Human review required")
