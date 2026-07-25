FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY common/ common/
COPY controlplane/ controlplane/

CMD ["uvicorn", "controlplane.main:app", "--host", "0.0.0.0", "--port", "8000"]