# Use a specific Python version on a slim base
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create the required directories
RUN mkdir -p ./.well-known

# Copy the application code
COPY app.py .

# Expose the Google ADK port
EXPOSE 8080

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Command to run the application using Gunicorn with increased timeout
CMD ["gunicorn", "--workers=4", "--timeout=120", "--bind=0.0.0.0:8080", "app:app"]