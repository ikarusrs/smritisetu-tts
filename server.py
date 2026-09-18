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

# Ensure voice models are downloaded
os.makedirs("/voices", exist_ok=True)

for name, model in VOICE_MAP.items():
    model_file = f"/voices/{model}.onnx"
    config_file = f"/voices/{model}.onnx.json"
    if not os.path.exists(model_file):
        logger.info(f"Downloading voice: {model}")
        base_url = f"https://huggingface.co/rhasspy/piper-voices/resolve/main"
        lang_short = model[:2]
        parts = model.split("-")
        voice_name = parts[2]
        quality = parts[3]
        url_base = f"{base_url}/{lang_short}/{model}/{voice_name}/{quality}"
        subprocess.run(["curl", "-sL", "-o", model_file, f"{url_base}/{model}.onnx"], check=True)
        subprocess.run(["curl", "-sL", "-o", config_file, f"{url_base}/{model}.onnx.json"], check=True)
        logger.info(f"Downloaded: {model}")


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

    model_path = f"/voices/{model}.onnx"
    logger.info(f"TTS request: lang={request.language}, model={model_path}")

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        cmd = ["piper", "--model", model_path, "--output_file", tmp_path]

        result = subprocess.run(
            cmd,
            input=request.text.encode("utf-8"),
            capture_output=True,
            timeout=60,
        )

        if result.returncode != 0:
            stderr = result.stderr.decode(errors="replace")
            logger.error(f"Piper error (rc={result.returncode}): {stderr}")
            raise HTTPException(status_code=500, detail=f"TTS generation failed: {stderr[:500]}")

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
