FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (this is just documentation, Cloud Run will set the actual port)
EXPOSE 8080

# Run the application - let Cloud Run set the PORT via environment variable
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}