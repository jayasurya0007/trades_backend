# Use the official Python base image
FROM python:3.11-slim

# Set environment variables to prevent .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 5000

# Run the Flask app using Gunicorn with 4 worker threads
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
