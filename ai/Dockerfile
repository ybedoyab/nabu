# AI Module Dockerfile - Nabu AI Processing
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app:/app/ai

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc g++ curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ai/ ./ai
COPY settings.py ./settings.py

# Create necessary directories
RUN mkdir -p /app/data /app/output /app/cache

# Run service from AI folder
WORKDIR /app/ai

# Download spaCy model
RUN python -m spacy download en_core_web_sm

# Health check — verify Python + core deps are importable
HEALTHCHECK --interval=60s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "from src.infrastructure.config import Config" || exit 1

# Keep container alive and idle, waiting for calls from the backend
CMD ["tail", "-f", "/dev/null"]
