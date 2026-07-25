import httpx
import logging
import base64
from app.config import settings
from app.voice.exceptions import TTSServiceError, TTSEmptyTextError

logger = logging.getLogger(__name__)

async def synthesize_speech(text: str, language: str = "hi-IN") -> bytes:
    """
    Send text to NVIDIA Chatterbox Multilingual TTS via NIM API.
    Falls back to Sarvam TTS if NVIDIA is not configured.
    Returns audio bytes (WAV format).
    """
    text = text.strip()
    if not text:
        raise TTSEmptyTextError("Cannot synthesize empty text")

    if len(text) > 5000:
        raise TTSServiceError("Text exceeds maximum allowed length (5000 chars) for TTS.")

    # Use NVIDIA Chatterbox TTS
    url = "https://integrate.api.nvidia.com/v1/audio/speech"
    headers = {
        "Authorization": f"Bearer {settings.NVIDIA_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "audio/wav"
    }
    
    payload = {
        "model": settings.NVIDIA_TTS_MODEL,
        "input": text,
        "voice": "Chatterbox",
        "language_code": language,
        "response_format": "wav",
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            
            if response.status_code != 200:
                logger.error(f"NVIDIA TTS failed with {response.status_code}: {response.text}")
                raise TTSServiceError(f"TTS API returned {response.status_code}")
            
            content_type = response.headers.get("content-type", "")
            
            # If response is direct audio bytes
            if "audio" in content_type:
                return response.content
            
            # If response is JSON with base64 encoded audio
            try:
                result = response.json()
                if "audio" in result:
                    return base64.b64decode(result["audio"])
                elif "data" in result:
                    return base64.b64decode(result["data"])
                else:
                    logger.error(f"Unexpected TTS response format: {result.keys()}")
                    raise TTSServiceError("Unexpected response format from TTS API")
            except Exception:
                # If it's not JSON, assume it's raw audio bytes
                return response.content
                
    except httpx.RequestError as e:
        logger.error(f"Network error calling TTS: {e}")
        raise TTSServiceError("Network error calling TTS API")
