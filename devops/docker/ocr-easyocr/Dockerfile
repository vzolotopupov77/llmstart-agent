FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --default-timeout=600 --retries=10 easyocr

WORKDIR /app
COPY ocr-common/preprocess.py /app/preprocess.py
COPY ocr-easyocr/run_batch.py /app/run_batch.py

ENV EASYOCR_MODULE_PATH=/models

ENTRYPOINT ["python", "/app/run_batch.py"]
