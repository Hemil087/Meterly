FROM python:3.12-slim

WORKDIR /app

# Install deps first — cached unless requirements.txt changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared module + service code
# Build context is repo root (set in docker-compose)
COPY common/ common/
COPY gateway/ gateway/

CMD ["uvicorn", "gateway.main:app", "--host", "0.0.0.0", "--port", "8001"]