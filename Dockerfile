# Use the official Python base image
FROM python:3.11-slim

# Set environment variables to prevent .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies (required for SQLite & gunicorn)
RUN apt-get update && apt-get install -y \
    gcc \
    libsqlite3-dev \
 && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source code
COPY . .

# Expose port (Render uses PORT env variable, but exposing 5000 is okay)
EXPOSE 5000

# Run the Flask app using Gunicorn with 4 workers
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
