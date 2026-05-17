# Use a secure, lightweight Python runtime
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy optimized catalogue and gold traces database
COPY shl_product_catalog_optimized.json .
COPY gold_standard_traces.json .

# Copy application source code
COPY catalog_loader.py .
COPY agent_service.py .
COPY main.py .

# Expose FastAPI server port
EXPOSE 8000

# Start FastAPI application using Uvicorn
CMD ["python", "main.py"]
