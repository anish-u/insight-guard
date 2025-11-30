FROM python:3.11-slim

WORKDIR /app

# Install system deps (if needed later for things like pandas, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
 && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY app ./app

# Non-root user (better practice)
RUN useradd -m appuser
USER appuser

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", \
     "--bind", "0.0.0.0:8000", "--workers", "4"]
