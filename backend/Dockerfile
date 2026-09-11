FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
ENV OMP_NUM_THREADS=1 \
	MKL_NUM_THREADS=1 \
	TOKENIZERS_PARALLELISM=false
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8000
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}