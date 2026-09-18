# SmritiSetu TTS Server

Piper TTS Docker server for SmritiSetu cognitive platform. Supports Assamese, Hindi, and English text-to-speech.

## Features

- FastAPI server with Piper TTS backend
- Supports Assamese (`as`), Hindi (`hi`), and English (`en`)
- Health check endpoint
- Docker-based deployment

## API Endpoints

### Health Check
```
GET /health
```

Response:
```json
{
  "status": "healthy",
  "voices": ["as", "hi", "en"]
}
```

### Text-to-Speech
```
POST /tts
Content-Type: application/json

{
  "text": "Hello world",
  "language": "en"
}
```

Supported languages:
- `as` - Assamese
- `hi` - Hindi
- `en` - English

Response: Audio/WAV binary data

## Docker Build

```bash
docker build -t smritisetu-tts .
docker run -p 8080:8080 smritisetu-tts
```

## Railway Deployment

1. Push to GitHub
2. Connect repository to Railway
3. Deploy automatically

## Environment Variables

- `PORT` - Server port (default: 8080)

## Voice Models

Uses Piper TTS with these voice models:
- `as_IN-arambha-medium` - Assamese
- `hi_IN-arambha-medium` - Hindi
- `en_US-lessac-medium` - English