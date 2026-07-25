import pytest
from unittest.mock import patch, MagicMock
import httpx
import base64
from app.voice.tts import synthesize_speech
from app.voice.exceptions import TTSEmptyTextError, TTSServiceError

@pytest.mark.asyncio
async def test_synthesize_speech_success():
    mock_audio_bytes = b"fake audio bytes"
    mock_base64 = base64.b64encode(mock_audio_bytes).decode('utf-8')
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"audios": [mock_base64]}
    
    with patch("httpx.AsyncClient.post", return_value=mock_response):
        result = await synthesize_speech("Hello there")
        assert result == mock_audio_bytes

@pytest.mark.asyncio
async def test_synthesize_speech_empty_text():
    with pytest.raises(TTSEmptyTextError):
        await synthesize_speech("   ")
        
@pytest.mark.asyncio
async def test_synthesize_speech_api_failure():
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = "Bad Request"
    
    with patch("httpx.AsyncClient.post", return_value=mock_response):
        with pytest.raises(TTSServiceError):
            await synthesize_speech("Hello there")
