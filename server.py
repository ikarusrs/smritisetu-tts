from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from piper import PiperVoice
import wave
import io
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

VOICE_MAP = {
    "as": "as_IN-arambha-medium",
    "hi": "hi_IN-arambha-medium",
    "en": "en_US-lessac-medium",
}

# Load all voice models at startup
voices = {}
for lang, model in VOICE_MAP.items():
    logger.info(f"Loading voice model: {model}")
    try:
        voices[lang] = PiperVoice.load(model, data_dir=["/voices"], download_dir="/voices")
        logger.info(f"Loaded: {model}")
    except Exception as e:
        logger.error(f"Failed to load {model}: {e}")


class TTSRequest(BaseModel):
    text: str
    language: str = "en"


@app.get("/health")
async def health_check():
    return {"status": "healthy", "voices": list(voices.keys())}


@app.post("/tts")
async def generate_tts(request: TTSRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    if len(request.text) > 500:
        raise HTTPException(status_code=400, detail="Text too long (max 500 characters)")

    voice = voices.get(request.language)
    if not voice:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {request.language}")

    logger.info(f"TTS request: lang={request.language}, len={len(request.text)}")

    try:
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wav_file:
            voice.synthesize(request.text, wav_file)
        buf.seek(0)
        audio_data = buf.read()
        logger.info(f"Generated {len(audio_data)} bytes")
        return Response(
            content=audio_data,
            media_type="audio/wav",
            headers={"Cache-Control": "no-store"},
        )
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail="TTS generation failed")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
