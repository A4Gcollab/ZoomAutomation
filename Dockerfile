# Python 3.10 slim image for small footprint
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies (ffmpeg is required for yt-dlp/processing)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create necessary volume mount points (optional, but good for documentation)
RUN mkdir -p /app/secrets /app/data /app/downloads

# Define volumes
VOLUME ["/app/secrets", "/app/data"]

# Run the application
CMD ["python", "-u", "main.py"]
