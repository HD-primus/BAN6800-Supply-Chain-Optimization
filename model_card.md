# Model Card — BAN6800 Late-Delivery Risk Classifier

**Version:** BAN6800-XGB-1.0  
**Model:** XGBoost binary classifier  
**Status:** Academic proof of concept; not approved for production  
**Dataset:** DataCo Smart Supply Chain public proxy, Module 3 cleaned table  
**Target:** `late_delivery` (1 = late; 0 = not late)  
**Decision threshold:** 0.40, selected using the validation period

## Intended use
Estimate the probability that a DataCo order-item record will be labelled late, to demonstrate predictive analytics and decision-support prioritisation. A high-risk flag may prompt a planner to review an order and consider additional monitoring or customer communication.

## Out-of-scope use
The model must not be represented as a Shell Petrochemicals model, used to allocate penalties, deny service, rank customers for exclusion, make employment or credit decisions, or operate without human review. The DataCo data are not Shell ERP, WMS or TMS records.

## Data and evaluation
The cleaned dataset contains 172,765 rows and 32 columns (one target and 31 candidate predictors). A chronological 64/16/20 split was used for model fitting, validation and final testing. The selected model was refitted on the first 80% after model selection. The final test period covers 22 April 2017 to 31 January 2018.

At threshold 0.40, final test results were: accuracy 0.6585; precision 0.6587; recall 0.8379; F1 0.7376; ROC-AUC 0.7789; PR-AUC 0.8582. Confusion matrix: TN 6,167; FP 8,592; FN 3,209; TP 16,585.

## Features
Order-time candidates include scheduled shipping days, discount rate, product price, item quantity, order timestamp components, transaction type, category, customer segment, department, market, order region, product name and shipping mode. Direct identifiers, target columns and post-outcome fields were excluded. High-cardinality city/state/country fields and realised profit/revenue fields were not included.

## Fairness and limitations
The dataset has no verified demographic protected attributes (for example age, sex or race). The analysis therefore compares operational groups only: Customer Segment, Market, Order Region and Shipping Mode. Observed flag-rate ratios and TPR/FPR gaps vary substantially, especially by order region and shipping mode. These are diagnostic screens, not legal or demographic fairness findings. Some test groups are absent from the later chronological holdout, so group coverage is incomplete.

A feature-ablation test shows ROC-AUC falls from 0.7789 to 0.5258 when both scheduled shipping days and shipping mode are removed. SHAP also identifies these variables as the strongest contributors. This concentration suggests dependence on dataset-specific scheduling structure. Validate with independent, point-in-time operational data before any real-world deployment.

## Explainability
Global SHAP importance and a local SHAP explanation are supplied. SHAP values describe how the fitted model uses input features; they do not establish causal effects. Counterfactual changes to protected or immutable attributes are not recommended.

## Human oversight and monitoring
A planner must review high-risk predictions before action. Monitor precision, recall, false-negative rates, calibration, feature drift, missingness, prediction rates and subgroup performance by segment, market, region and shipping mode. Investigate sudden changes and maintain a documented rollback path. Revalidate the model when operational policies, shipping modes, customer mix or data definitions change.
