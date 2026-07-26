import google.generativeai as genai
from app.config import settings
from app.voice.exceptions import STTEmptyResultError

async def transcribe_audio(audio_bytes: bytes, language_hint: str = "hi-IN") -> str:
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = "Transcribe the following audio accurately. It may be in Hindi, English, or mixed. If it is empty or silent, return an empty string. Only return the transcription text, no extra formatting or explanations."
    content_parts = {"mime_type": "audio/webm", "data": audio_bytes}
    
    try:
        response = await model.generate_content_async([prompt, content_parts])
        text = response.text.strip()
        if not text:
            raise STTEmptyResultError("Empty transcription")
        return text
    except Exception as e:
        if isinstance(e, STTEmptyResultError):
            raise
        raise Exception(f"Transcription failed: {e}")
