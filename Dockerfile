# Matches the project's required interpreter (3.10 — faiss/torch wheels
# target it; system 3.14 is not compatible).
FROM python:3.10-slim

WORKDIR /app

# faiss-cpu and sentence-transformers pull in some native deps that need a
# compiler toolchain when no prebuilt wheel matches; keep the image slim
# otherwise.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY scripts ./scripts
COPY data/raw ./data/raw
COPY data/eval/qa_set.json ./data/eval/qa_set.json

# Pre-build the FAISS + BM25 index at image build time so the container is
# ready to serve immediately. Rebuild the image (or re-run
# scripts/build_index.py) whenever data/raw changes.
RUN python scripts/build_index.py

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
