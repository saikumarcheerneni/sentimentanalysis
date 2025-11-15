# Use official Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy ONLY requirements first
COPY requirements.txt /app/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the rest of the project
COPY . /app

# Expose port
EXPOSE 80

# Start the app using Gunicorn + Uvicorn worker
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:80"]
