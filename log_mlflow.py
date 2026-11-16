"""Log the completed local experiment records and artifacts to a real MLflow store.
Run after installing MLflow: python src/log_mlflow.py
"""
from pathlib import Path
import json
import mlflow
ROOT=Path(__file__).resolve().parents[1]
record=json.loads((ROOT/'tracking'/'experiment_run_record.json').read_text())
mlflow.set_tracking_uri("http://127.0.0.1:5000")
mlflow.set_experiment('BAN6800_Supply_Chain_Late_Delivery')
for item in record['model_comparison_validation']:
    with mlflow.start_run(run_name='validation_'+item['model'].lower().replace(' ','_')):
        mlflow.log_param('model',item['model'])
        for k,v in item.items():
            if k!='model' and v is not None:
                try:
                    if v==v: mlflow.log_metric(k,float(v))
                except (TypeError,ValueError): pass
        mlflow.set_tag('dataset','DataCo Smart Supply Chain public proxy')
        mlflow.set_tag('split','chronological validation')
with mlflow.start_run(run_name='selected_xgboost_final_test'):
    mlflow.log_param('model','XGBoost')
    mlflow.log_param('n_estimators',120); mlflow.log_param('max_depth',4)
    mlflow.log_param('learning_rate',0.06); mlflow.log_param('decision_threshold',0.40)
    for k,v in record['selected_model_test_metrics'].items():
        if isinstance(v,(int,float)) and v==v: mlflow.log_metric(k,float(v))
    mlflow.set_tag('split','untouched chronological test period')
    for path in [ROOT/'models'/'model_bundle.joblib',ROOT/'reports'/'model_validation_metrics.json',
                 ROOT/'reports'/'fairness_summary.csv',ROOT/'reports'/'shap_global_importance.csv']:
        if path.exists(): mlflow.log_artifact(str(path),artifact_path='validation_pack')
print('MLflow tracking complete. Start the UI with: mlflow ui --backend-store-uri ./mlruns')
