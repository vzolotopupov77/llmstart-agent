FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-rus \
        tesseract-ocr-eng \
        libgl1 \
        libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --default-timeout=120 --retries=5 pillow

WORKDIR /app
COPY ocr-common/preprocess.py /app/preprocess.py
COPY ocr-tesseract/run_batch.py /app/run_batch.py

ENTRYPOINT ["python", "/app/run_batch.py"]
