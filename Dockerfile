FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    libev-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*  # Clean up apt cache

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 8000
CMD ["uvicorn", "service.app:app", "--host", "0.0.0.0", "--port", "8000"]