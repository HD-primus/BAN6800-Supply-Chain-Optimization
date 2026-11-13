# BAN6800 Module 3 — Reproducible Data Pipeline (Actual DataCo Run)

## Project context
This is an academic proof of concept for the Module 1/2 project, **Prescriptive Supply Chain Optimization and Bottleneck Analytics Platform**. The DataCo Smart Supply Chain dataset is a public proxy; it is not Shell Petrochemicals' internal data. The Module 1 improvement figures (22% fewer delays, 15% lower inventory holding costs, OTIF 81% to 94%) remain proposed targets, not measured outcomes.

## Files supplied
- `src/pipeline.py`: ingestion, cleaning, label checks, privacy/leakage exclusions, publication and reports.
- `src/gx_validate.py`: optional Great Expectations 0.18.x validation runner. It was not executed in this environment.
- `src/bias_audit.py`: descriptive coverage report by selected operational groups; not a fairness certification.
- `dags/dataco_pipeline_dag.py`: Airflow DAG wrapper. It was not executed in this environment.
- `tests/test_pipeline.py`: three unit tests; all passed locally.
- `reports/`: actual source profile, missingness, schema profile, dictionary crosswalk, group coverage and pipeline validation.
- `logs/privacy_audit.jsonl`: a run-level audit record containing hashes and counts, not customer values.
- `data/processed/model_ready.csv.gz`: actual cleaned data for Module 4.

The raw CSV is deliberately not included in this ZIP because it contains direct customer identifiers. Keep it in a restricted local data folder and do not commit it to a public GitHub repository.

## Actual source profile
- Source file: 180,519 rows × 53 columns; read using Latin-1 encoding.
- Exact duplicate rows: 0. `Order Item Id` is unique across all 180,519 rows.
- Date fields: all 180,519 values parsed successfully for each date field.
- Missingness: `Product Description` 100%; `Order Zipcode` 86.24%; `Customer Lname` 8; `Customer Zipcode` 3. `Product Description` and direct/granular identifiers are excluded from the model table.
- Dictionary: 52 documented field entries versus 53 source columns. All fields match after trimming whitespace and case-normalising except `Order Zipcode`, which is not described in the supplied dictionary. `shipping date (DateOrders)` matches dictionary entry `Shipping date (DateOrders)` after case normalisation.

## Target definition and key decision
The dictionary defines `Late_delivery_risk` as a categorical indicator (1 late, 0 not late). In the uploaded file it matches `Delivery Status == 'Late delivery'` for all 180,519 source rows. The pipeline excludes 7,754 `Shipping canceled` records because they are not completed delivery outcomes, then uses `Late_delivery_risk` as the target and removes both label fields from predictors.

A naive rule `Days for shipping (real) > Days for shipment (scheduled)` disagrees with `Late_delivery_risk` on 4,423 records; all 4,423 are cancelled shipments. This is why the comparison is not used as the target. `Days for shipping (real)`, shipping date, `Delivery Status`, `Late_delivery_risk`, and `Order Status` are excluded from predictors to reduce post-outcome/label leakage.

## Actual output
- 172,765 retained records × 32 columns (1 target + 31 candidate predictors).
- Target counts: 98,977 late (1); 73,788 not late (0).
- No missing values in the published model-ready table.
- Eight local pandas validation assertions pass; three pytest unit tests pass.
- Great Expectations 0.18.21 suite executed on 2026-11-13: 4 of 4 expectations passed.
- The data output is compressed CSV, not Parquet; Parquet was not created in this run.

## Run locally
1. Create a Python 3.11 environment.
2. Install `pandas==2.2.3` and `pytest==8.3.4`.
3. Place the raw file at `data/DataCoSupplyChainDataset.csv` (do not commit it).
4. Run:
   ```bash
   python -m src.pipeline --input data/DataCoSupplyChainDataset.csv --output data/processed/model_ready.csv.gz --reports reports
   python -m pytest -q
   ```
5. Optional Great Expectations check after installing `great-expectations==0.18.21`:
   ```bash
   python -m src.gx_validate data/processed/model_ready.csv.gz
   ```
6. For Airflow, install a compatible Airflow release using its official constraints file, set `DATACO_INPUT`, `DATACO_OUTPUT`, and `DATACO_REPORTS`, then load `dags/dataco_pipeline_dag.py`. Airflow was not run in this deliverable.

## Governance and Module 4 hand-off
- Direct customer identifiers, customer names/email/password/street, customer IDs, exact customer/postal coordinates and order/item keys are excluded from the model-ready table.
- No hashing is needed for the current feature table because customer-level linkage is not required; do not retain raw credentials or secrets.
- Use role-based least privilege, encryption at rest/in transit, restricted raw-data access, documented retention and deletion, and audit logging in a production environment.
- `Customer Segment`, `Market`, `Order Region`, and `Shipping Mode` can be used for descriptive representation checks. Actual subgroup error-rate/fairness analysis belongs after Module 4 model evaluation.
- DataCo lacks Shell ERP/WMS/TMS operational records, true Shell inventory costs and confirmed OTIF baselines. Therefore the current dataset cannot validate Shell-specific savings, OTIF improvement or the proposed 14-day operational forecast.

## References
Constante, F., Silva, F., & Pereira, A. (2019). *DataCo SMART SUPPLY CHAIN FOR BIG DATA ANALYSIS* (Version 1) [Data set]. Mendeley Data. https://doi.org/10.17632/8gx2fvg2k6.1

National Institute of Standards and Technology. (2023). *Artificial Intelligence Risk Management Framework (AI RMF 1.0).* https://doi.org/10.6028/NIST.AI.100-1

Federal Republic of Nigeria. (2023). *Nigeria Data Protection Act, 2023.*
