import google.generativeai as genai
from app.config import settings
from app.voice.exceptions import STTEmptyResultError

def _clean_mime_type(mime_type: str) -> str:
    if not mime_type:
        return "audio/webm"
    clean = mime_type.split(";")[0].strip().lower()
    if clean in ["audio/webm", "audio/mp4", "audio/wav", "audio/mp3", "audio/mpeg", "audio/ogg", "audio/aac", "audio/m4a", "audio/flac"]:
        return clean
    if "webm" in clean:
        return "audio/webm"
    if "mp4" in clean or "m4a" in clean:
        return "audio/mp4"
    if "ogg" in clean:
        return "audio/ogg"
    if "wav" in clean:
        return "audio/wav"
    return "audio/webm"

async def transcribe_audio(audio_bytes: bytes, language_hint: str = "hi-IN", mime_type: str = "audio/webm") -> str:
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = "Transcribe the following audio accurately. It may be in Hindi, English, or mixed. If it is empty or silent, return an empty string. Only return the transcription text, no extra formatting or explanations."
    
    import tempfile
    import os
    
    # Save to temp file
    ext = ".webm" if "webm" in mime_type else ".mp4"
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_audio:
        temp_audio.write(audio_bytes)
        temp_path = temp_audio.name
        
    try:
        # Upload using File API (treat as video/webm to ensure compatibility)
        uploaded_file = genai.upload_file(temp_path, mime_type="video/webm" if "webm" in ext else "video/mp4")
        
        response = await model.generate_content_async([prompt, uploaded_file])
        text = response.text.strip() if response and response.text else ""
        
        # Cleanup from Gemini
        try:
            uploaded_file.delete()
        except:
            pass
            
        if not text:
            raise STTEmptyResultError("Empty transcription")
        return text
    except Exception as e:
        if isinstance(e, STTEmptyResultError):
            raise
        raise Exception(f"Transcription failed: {e}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
