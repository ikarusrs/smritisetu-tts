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

# Pre-download voice models
RUN python3 -c "\
from piper.download import get_voices, ensure_voice_exists, find_voice; \
import os; \
voices_info = get_voices('/voices', update_voices=True); \
for v in ['as_IN-arambha-medium', 'hi_IN-arambha-medium', 'en_US-lessac-medium']; \
    ensure_voice_exists(v, ['/voices'], '/voices', voices_info); \
print('Done downloading voices')" || echo "Download step completed with warnings"

# Copy application code
COPY server.py .

# Expose port 8080
EXPOSE 8080

# Run the server
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]
