FROM python:3.11-slim

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY web_api/requirements.txt .
RUN pip install --no-cache-dir --default-timeout=1000 -r requirements.txt

COPY . .

CMD ["python", "-m", "uvicorn", "web_api.main:app", "--host", "0.0.0.0", "--port", "8000"]