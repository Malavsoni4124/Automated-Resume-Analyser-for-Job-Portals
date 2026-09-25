FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for ML libraries
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Download Spacy model
RUN python -m spacy download en_core_web_md

# Copy application code
COPY . .

# Expose the API port
EXPOSE 8000

# Start the application (Respecting PORT env variable for PaaS like Render)
CMD uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8000}
