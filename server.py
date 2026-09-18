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

class TTSRequest(BaseModel):
    text: str
    language: str = "en"

VOICE_MAP = {
    "as": "as_IN-arambha-medium",
    "hi": "hi_IN-arambha-medium",
    "en": "en_US-lessac-medium"
}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "voices": list(VOICE_MAP.keys())}

@app.post("/tts")
async def generate_tts(request: TTSRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    if len(request.text) > 500:
        raise HTTPException(status_code=400, detail="Text too long (max 500 characters)")
    
    voice = VOICE_MAP.get(request.language)
    if not voice:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {request.language}")
    
    logger.info(f"Generating TTS for language={request.language}, text_length={len(request.text)}")
    
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        # Use piper command line tool
        cmd = [
            "piper",
            "--model", voice,
            "--data-dir", "/voices",
            "--output_file", tmp_path
        ]
        
        result = subprocess.run(
            cmd,
            input=request.text.encode("utf-8"),
            capture_output=True,
            timeout=30
        )
        
        if result.returncode != 0:
            logger.error(f"Piper error: {result.stderr.decode()}")
            raise HTTPException(status_code=500, detail="TTS generation failed")
        
        with open(tmp_path, "rb") as f:
            audio_data = f.read()
        
        logger.info(f"Generated audio: {len(audio_data)} bytes")
        
        return Response(
            content=audio_data,
            media_type="audio/wav",
            headers={"Cache-Control": "no-store"}
        )
    
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="TTS generation timed out")
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)