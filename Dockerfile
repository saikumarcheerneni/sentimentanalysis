# Use official Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements first (to control caching)
COPY requirements.txt /app/requirements.txt

# Use PyTorch CPU wheel index + no cache
ENV PIP_NO_CACHE_DIR=1
ENV PIP_EXTRA_INDEX_URL=https://download.pytorch.org/whl/cpu

# Install dependencies
RUN pip install --upgrade pip && \
    pip install -r /app/requirements.txt

# Copy full project
COPY . /app

# Expose port
EXPOSE 8000

# Start uvicorn via gunicorn
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
