from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
import subprocess
import tempfile
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

VOICE_MAP = {
    "hi": "hi_IN-pratham-medium",
    "en": "en_US-lessac-medium",
}


class TTSRequest(BaseModel):
    text: str
    language: str = "en"


@app.get("/health")
async def health_check():
    return {"status": "healthy", "voices": list(VOICE_MAP.keys())}


@app.post("/tts")
async def generate_tts(request: TTSRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    if len(request.text) > 500:
        raise HTTPException(status_code=400, detail="Text too long (max 500 characters)")

    model = VOICE_MAP.get(request.language)
    if not model:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {request.language}")

    logger.info(f"TTS request: lang={request.language}, len={len(request.text)}")

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        cmd = [
            "piper",
            "--model", model,
            "--output_file", tmp_path,
        ]

        result = subprocess.run(
            cmd,
            input=request.text.encode("utf-8"),
            capture_output=True,
            timeout=60,
        )

        if result.returncode != 0:
            stderr = result.stderr.decode(errors="replace")
            logger.error(f"Piper error: {stderr}")
            raise HTTPException(status_code=500, detail=f"TTS generation failed: {stderr[:200]}")

        with open(tmp_path, "rb") as f:
            audio_data = f.read()

        logger.info(f"Generated {len(audio_data)} bytes")
        return Response(
            content=audio_data,
            media_type="audio/wav",
            headers={"Cache-Control": "no-store"},
        )

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="TTS generation timed out")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
