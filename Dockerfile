FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir pandas==2.2.3 pytest==8.3.4
COPY src ./src
COPY tests ./tests
COPY reports ./reports
RUN mkdir -p data/processed
ENV PYTHONPATH=/app
CMD ["python", "-m", "src.pipeline", "--input", "/app/data/DataCoSupplyChainDataset.csv", "--output", "/app/data/processed/model_ready.csv.gz", "--reports", "/app/reports"]
