FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Piper TTS and server dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create voice directory
RUN mkdir -p /voices

# Pre-download Assamese, Hindi, and English voices
RUN python3 -c "from piper import PiperVoice; \
    PiperVoice.load('as_IN-arambha-medium', download_dir='/voices', data_dir=['/voices'])" || true && \
    python3 -c "from piper import PiperVoice; \
    PiperVoice.load('hi_IN-arambha-medium', download_dir='/voices', data_dir=['/voices'])" || true && \
    python3 -c "from piper import PiperVoice; \
    PiperVoice.load('en_US-lessac-medium', download_dir='/voices', data_dir=['/voices'])" || true

# Copy application code
COPY server.py .

# Expose port 8080
EXPOSE 8080

# Run the server
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]