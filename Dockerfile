# Use official Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements first (to control caching)
COPY requirements.txt /app/requirements.txt

# Install dependencies (force reinstall to avoid Azure cache issues)
RUN pip install --no-cache-dir --upgrade --force-reinstall -r /app/requirements.txt

# Copy entire project
COPY . /app

# Expose port
EXPOSE 8000

# Start uvicorn via gunicorn
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
