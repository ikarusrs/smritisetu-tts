FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Piper TTS
RUN pip install piper-tts

# Create voice directory
RUN mkdir -p /voices

# Download Assamese, Hindi, and English voices
RUN piper download --voice as_IN-arambha-medium --data-dir /voices && \
    piper download --voice hi_IN-arambha-medium --data-dir /voices && \
    piper download --voice en_US-lessac-medium --data-dir /voices

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY server.py .

# Expose port 8080
EXPOSE 8080

# Run the server
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]