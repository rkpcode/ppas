import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from app.main import app
from app.models.staff import Staff
from app.services.auth_service import get_current_user
from app.voice.exceptions import STTEmptyResultError, STTServiceError

# Mock dependencies
async def mock_get_current_user():
    return Staff(id=1, username="test_staff", role="pharmacist", is_active=True)

app.dependency_overrides[get_current_user] = mock_get_current_user

client = TestClient(app)

@pytest.fixture
def mock_pipeline():
    with patch("app.api.v1.voice.transcribe_audio", new_callable=AsyncMock) as mock_stt, \
         patch("app.api.v1.voice.run_inventory_agent") as mock_agent, \
         patch("app.api.v1.voice.synthesize_speech", new_callable=AsyncMock) as mock_tts:
         
        yield mock_stt, mock_agent, mock_tts

def test_voice_query_success(mock_pipeline):
    mock_stt, mock_agent, mock_tts = mock_pipeline
    
    mock_stt.return_value = "paracetamol hai kya?"
    mock_agent.return_value = "Haan sir, paracetamol stock mein hai."
    mock_tts.return_value = b"fake audio response"
    
    response = client.post(
        "/voice/query",
        files={"file": ("test.wav", b"fake user audio", "audio/wav")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["transcribed_text"] == "paracetamol hai kya?"
    assert data["agent_response_text"] == "Haan sir, paracetamol stock mein hai."
    assert "audio_base64" in data
    
    mock_stt.assert_called_once()
    mock_agent.assert_called_once_with("paracetamol hai kya?")
    mock_tts.assert_called_once_with("Haan sir, paracetamol stock mein hai.", language="hi-IN")

def test_voice_query_stt_empty_fallback(mock_pipeline):
    mock_stt, mock_agent, mock_tts = mock_pipeline
    
    mock_stt.side_effect = STTEmptyResultError()
    mock_tts.return_value = b"fake fallback audio"
    
    response = client.post(
        "/voice/query",
        files={"file": ("test.wav", b"silent audio", "audio/wav")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["transcribed_text"] == ""
    assert data["agent_response_text"] == "Sir, samjha nahi, dobara boliye."
    
    mock_stt.assert_called_once()
    mock_agent.assert_not_called()
    mock_tts.assert_called_once_with("Sir, samjha nahi, dobara boliye.", language="hi-IN")

def test_voice_query_stt_failure_graceful_fallback(mock_pipeline):
    mock_stt, mock_agent, mock_tts = mock_pipeline
    
    mock_stt.side_effect = STTServiceError()
    mock_tts.return_value = b"fake error fallback audio"
    
    response = client.post(
        "/voice/query",
        files={"file": ("test.wav", b"some audio", "audio/wav")}
    )
    
    # Even on STT failure, it returns a 200 with the fallback audio and text
    assert response.status_code == 200
    data = response.json()
    assert data["agent_response_text"] == "Voice system thoda slow hai, dobara try kariye."
    
    mock_tts.assert_called_once_with("Voice system thoda slow hai, dobara try kariye.", language="hi-IN")
