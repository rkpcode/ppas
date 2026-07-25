import sounddevice as sd
import numpy as np
import keyboard
import time
import logging
import wave
import io
from app.config import settings

logger = logging.getLogger(__name__)

def record_on_hotkey(hotkey: str = None, max_duration_seconds: int = 15) -> bytes:
    """
    Listens for the configured hotkey. While held, records audio from the default microphone.
    Returns raw audio bytes (WAV format) ready to pass to transcribe_audio().
    """
    if hotkey is None:
        hotkey = settings.PUSH_TO_TALK_HOTKEY

    samplerate = 16000  # Sarvam STT commonly accepts 16kHz
    channels = 1
    
    logger.info(f"Waiting for hotkey '{hotkey}' to start recording...")
    
    # Block until key is pressed
    keyboard.wait(hotkey)
    
    logger.info(f"Hotkey '{hotkey}' pressed. Recording started...")
    
    frames = []
    
    def callback(indata, frames_count, time_info, status):
        if status:
            logger.warning(f"Audio status: {status}")
        frames.append(indata.copy())

    stream = sd.InputStream(samplerate=samplerate, channels=channels, callback=callback)
    
    with stream:
        start_time = time.time()
        # Loop while the key is pressed and max duration is not reached
        while keyboard.is_pressed(hotkey):
            if time.time() - start_time > max_duration_seconds:
                logger.warning(f"Max recording duration ({max_duration_seconds}s) reached. Stopping.")
                break
            time.sleep(0.05)
            
    logger.info("Recording stopped.")
    
    if not frames:
        return b""
        
    # Convert frames to numpy array
    audio_data = np.concatenate(frames, axis=0)
    
    # Convert numpy array to WAV bytes
    wav_io = io.BytesIO()
    with wave.open(wav_io, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2) # 2 bytes = 16 bit
        wf.setframerate(samplerate)
        # Convert float32 (default sd format) to int16
        audio_int16 = (audio_data * 32767).astype(np.int16)
        wf.writeframes(audio_int16.tobytes())
        
    return wav_io.getvalue()
