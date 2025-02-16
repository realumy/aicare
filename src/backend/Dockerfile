# Use an official Python 3.11 (or any other version) base image
FROM python:3.11-slim

# Install system dependencies including PortAudio dev
RUN apt-get update && apt-get install -y --no-install-recommends && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
COPY .. .

# Start FastAPI with uvicorn on port 3000
CMD uvicorn app:app --host 0.0.0.0 --port $PORT
