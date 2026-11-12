"""Airflow wrapper. This DAG is supplied but was not executed in this workspace."""
from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
import os
from src.pipeline import run

INPUT = os.getenv("DATACO_INPUT", "/opt/airflow/data/DataCoSupplyChainDataset.csv")
OUTPUT = os.getenv("DATACO_OUTPUT", "/opt/airflow/data/processed/model_ready.csv.gz")
REPORTS = os.getenv("DATACO_REPORTS", "/opt/airflow/reports")

def execute_pipeline():
    run(INPUT, OUTPUT, REPORTS)

with DAG(
    dag_id="dataco_supply_chain_pipeline",
    description="Batch ETL, quality validation and model-ready publication for BAN6800",
    start_date=datetime(2026, 1, 1), schedule=None, catchup=False,
    tags=["BAN6800", "DataCo", "ETL"],
) as dag:
    process_validate_publish = PythonOperator(
        task_id="process_validate_publish",
        python_callable=execute_pipeline,
    )
