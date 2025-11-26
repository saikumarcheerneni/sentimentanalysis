# Use official Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements first (to control caching)
COPY requirements.txt /app/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir --upgrade --force-reinstall -r /app/requirements.txt

# Copy full project
COPY . /app

# Load Azure App Service ENV variables into container
ENV SENDGRID_API_KEY=${SENDGRID_API_KEY}
ENV SENDGRID_FROM_EMAIL=${SENDGRID_FROM_EMAIL}
ENV APP_BASE_URL=${APP_BASE_URL}
ENV MONGO_URI=${MONGO_URI}
ENV SECRET_KEY=${SECRET_KEY}

# Expose port
EXPOSE 8000

# Start uvicorn via gunicorn
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
