from app.exceptions.base import PharmacyBaseException

class STTEmptyResultError(PharmacyBaseException):
    """No speech detected in audio — likely silence or pure noise."""
    def __init__(self, message: str = "No speech detected in audio.", status_code: int = 400):
        super().__init__(message=message, code="STT_EMPTY_RESULT", status_code=status_code)

class STTServiceError(PharmacyBaseException):
    """Sarvam STT API call failed (network, auth, rate limit, etc.)."""
    def __init__(self, message: str = "Speech-to-text service failed.", status_code: int = 502):
        super().__init__(message=message, code="STT_SERVICE_ERROR", status_code=status_code)

class TTSServiceError(PharmacyBaseException):
    """Sarvam TTS API call failed."""
    def __init__(self, message: str = "Text-to-speech service failed.", status_code: int = 502):
        super().__init__(message=message, code="TTS_SERVICE_ERROR", status_code=status_code)

class TTSEmptyTextError(PharmacyBaseException):
    """Attempted to synthesize empty or whitespace-only text."""
    def __init__(self, message: str = "Attempted to synthesize empty text.", status_code: int = 400):
        super().__init__(message=message, code="TTS_EMPTY_TEXT", status_code=status_code)
