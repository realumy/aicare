# Use an official Python 3.11 (or any other version) base image
FROM python:3.11-slim

# 1. Install packages needed for PyAudio (PortAudio dev and gcc/build tools).
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    portaudio19-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
COPY .. .

# Koyeb listens on port 3000 by default, so expose 3000
EXPOSE 8000

# Start FastAPI with uvicorn on port 3000
CMD ["streamlit", "run", "aicare_front.py"]

