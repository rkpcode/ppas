import httpx
import logging
from app.config import settings
from app.voice.exceptions import STTEmptyResultError, STTServiceError

logger = logging.getLogger(__name__)

async def transcribe_audio(audio_bytes: bytes, language_hint: str = "auto") -> str:
    """
    Send audio to Sarvam STT, return transcribed text.

    language_hint: "hi-IN" (Hindi), "or-IN" (Odia), or "auto"
    """
    if not audio_bytes:
        raise STTEmptyResultError("Empty audio provided")

    url = "https://api.sarvam.ai/speech-to-text"
    headers = {
        "api-subscription-key": settings.SARVAM_API_KEY
    }
    
    # We use mode="transcribe", model="saaras:v3" as per Sarvam docs.
    data = {
        "model": settings.SARVAM_STT_MODEL,
        "mode": "transcribe"
    }
    if language_hint != "auto":
        data["language_code"] = language_hint

    files = {
        "file": ("audio.wav", audio_bytes, "audio/wav")
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, headers=headers, data=data, files=files)
            
            if response.status_code != 200:
                logger.error(f"Sarvam STT failed with {response.status_code}: {response.text}")
                raise STTServiceError(f"STT API returned {response.status_code}")
                
            result = response.json()
            # Log metadata but not transcript at info level
            logger.debug(f"STT Full Result: {result}")
            
            # The transcript key might be 'transcript' or something similar in Sarvam API.
            # Usually it's {"transcript": "..."}
            transcript = result.get("transcript", "").strip()
            
            if not transcript:
                raise STTEmptyResultError("Sarvam returned empty transcription")
                
            return transcript
            
    except httpx.RequestError as e:
        logger.error(f"Network error calling STT: {e}")
        raise STTServiceError("Network error calling STT API")
