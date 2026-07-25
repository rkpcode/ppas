import pytest
from unittest.mock import patch, MagicMock
import httpx
from app.voice.stt import transcribe_audio
from app.voice.exceptions import STTEmptyResultError, STTServiceError

@pytest.mark.asyncio
async def test_transcribe_audio_success():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"transcript": "नमस्ते"}
    
    with patch("httpx.AsyncClient.post", return_value=mock_response):
        result = await transcribe_audio(b"fake audio data")
        assert result == "नमस्ते"

@pytest.mark.asyncio
async def test_transcribe_audio_empty_audio_bytes():
    with pytest.raises(STTEmptyResultError):
        await transcribe_audio(b"")

@pytest.mark.asyncio
async def test_transcribe_audio_empty_transcription():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"transcript": "   "}
    
    with patch("httpx.AsyncClient.post", return_value=mock_response):
        with pytest.raises(STTEmptyResultError):
            await transcribe_audio(b"fake audio data")

@pytest.mark.asyncio
async def test_transcribe_audio_api_failure():
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    
    with patch("httpx.AsyncClient.post", return_value=mock_response):
        with pytest.raises(STTServiceError):
            await transcribe_audio(b"fake audio data")

@pytest.mark.asyncio
async def test_transcribe_audio_network_error():
    with patch("httpx.AsyncClient.post", side_effect=httpx.RequestError("Network error")):
        with pytest.raises(STTServiceError):
            await transcribe_audio(b"fake audio data")
