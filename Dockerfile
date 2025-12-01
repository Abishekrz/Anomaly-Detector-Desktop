# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["python", "-u", "detection_service.py"]
# detection_service.py would be a minimal Flask/FastAPI wrapper you can create to expose endpoints.
