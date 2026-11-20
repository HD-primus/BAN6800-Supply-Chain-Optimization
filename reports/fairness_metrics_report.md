# Fairness Metrics Report

## Scope
The cleaned DataCo table does not contain verified demographic protected attributes such as age, sex or race. Therefore, demographic parity and equalized-odds claims about protected classes cannot be made. The analysis below uses operational proxy groups already identified in the project fairness objective: Customer Segment, Market, Order Region and Shipping Mode. These variables are not substitutes for legally protected attributes.

## Outcome definition
The positive model decision (`high_risk_flag = 1`) is interpreted as an invitation for additional planner attention/support, not a negative customer decision. The disparate-impact-style ratio is the minimum group high-risk flag rate divided by the maximum group rate within each dimension. It is a screening statistic only; because support allocation is the favourable action, its interpretation differs from adverse-impact screening in hiring or lending.

## Results on the untouched chronological test set

| Operational dimension | Observed groups | Min/max flag-rate ratio | TPR gap | FPR gap |
|---|---:|---:|---:|---:|
| Customer Segment | 3 | 0.905 | 0.046 | 0.103 |
| Market | 3 | 0.789 | 0.124 | 0.216 |
| Order Region | 10 | 0.404 | 0.366 | 0.695 |
| Shipping Mode | 4 | 0.529 | 0.394 | 1.000 |

The group-level CSV contains group sizes, observed late rates, flag rates, precision, TPR, FPR and accuracy. Market and regional categories not represented in the later test window cannot be assessed in this split. Some shipping-mode categories have very different observed base rates, including a 100% late label rate for First Class in this dataset. This may be a dataset or policy artefact and makes simple parity comparisons misleading.

## Interpretation and response
The results show material operational-group differences, particularly for region and shipping mode. They do not prove discriminatory treatment because the dataset has no protected demographic labels and group outcome rates differ. Before deployment, collect appropriately governed and legally permitted group data where justified, improve representation for under-covered groups, review proxy features and assess subgroup confidence intervals. If a disparity persists, test reweighting or constrained threshold/post-processing approaches on a validation set, then compare accuracy, recall, precision and group error rates. Do not change thresholds solely to force a ratio without considering the operational consequences. Keep human review and appeal mechanisms in place.
