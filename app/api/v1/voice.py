import time
import logging
import base64
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Annotated
from app.models.staff import Staff
from app.services.auth_service import get_current_user
from app.agents.inventory_agent.graph import run_inventory_agent
from app.voice.stt import transcribe_audio
from app.voice.tts import synthesize_speech
from app.voice.exceptions import STTEmptyResultError, STTServiceError, TTSServiceError, TTSEmptyTextError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice", tags=["Voice"])

class VoiceResponse(BaseModel):
    transcribed_text: str
    agent_response_text: str
    audio_base64: str
    
@router.post("/query", response_model=VoiceResponse)
async def voice_query(
    current_user: Annotated[Staff, Depends(get_current_user)],
    file: UploadFile = File(...)
):
    start_total = time.time()
    
    # 1. Read uploaded audio bytes
    audio_bytes = await file.read()
    
    transcribed_text = ""
    agent_response_text = ""
    audio_base64 = ""
    
    try:
        # 2. Call transcribe_audio()
        start_stt = time.time()
        try:
            transcribed_text = await transcribe_audio(audio_bytes, language_hint="hi-IN")
            stt_duration = time.time() - start_stt
            logger.info(f"STT Duration: {stt_duration:.2f}s")
            
            # 3. Pass transcribed text to run_inventory_agent
            start_agent = time.time()
            agent_response_text = run_inventory_agent(transcribed_text)
            agent_duration = time.time() - start_agent
            logger.info(f"Agent Duration: {agent_duration:.2f}s")
            
        except STTEmptyResultError:
            # Fallback for silence
            agent_response_text = "Sir, samjha nahi, dobara boliye."
            logger.info("STT returned empty result. Using fallback message.")
            
        # 4. Synthesize speech on the response text
        start_tts = time.time()
        response_audio_bytes = await synthesize_speech(agent_response_text, language="hi-IN")
        tts_duration = time.time() - start_tts
        logger.info(f"TTS Duration: {tts_duration:.2f}s")
        
        audio_base64 = base64.b64encode(response_audio_bytes).decode('utf-8')
        
    except Exception as e:
        logger.error(f"Error in voice pipeline: {str(e)}")
        
        # Attempt to synthesize a fallback message on any error
        fallback_msg = "Voice system thoda slow hai, dobara try kariye."
        try:
            fallback_audio = await synthesize_speech(fallback_msg, language="hi-IN")
            audio_base64 = base64.b64encode(fallback_audio).decode('utf-8')
            agent_response_text = fallback_msg
        except Exception as tts_e:
            logger.error(f"Failed to synthesize fallback message: {str(tts_e)}")
            # Raise if we can't even synthesize fallback
            raise HTTPException(status_code=500, detail="Voice pipeline failed completely.")
    
    total_duration = time.time() - start_total
    logger.info(f"Total Pipeline Duration: {total_duration:.2f}s")
    
    return VoiceResponse(
        transcribed_text=transcribed_text,
        agent_response_text=agent_response_text,
        audio_base64=audio_base64
    )
