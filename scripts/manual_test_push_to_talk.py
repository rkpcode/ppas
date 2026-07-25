import os
import sys
import httpx
import base64
import sounddevice as sd
import wave
import numpy as np
import io
import asyncio

# Add parent dir to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.voice.push_to_talk import record_on_hotkey
from app.services.auth_service import create_access_token

def play_audio(audio_bytes):
    try:
        with wave.open(io.BytesIO(audio_bytes), 'rb') as wf:
            samplerate = wf.getframerate()
            # Convert bytes to numpy array for sounddevice
            raw_data = wf.readframes(wf.getnframes())
            audio_data = np.frombuffer(raw_data, dtype=np.int16)
            
        print("Playing response...")
        sd.play(audio_data, samplerate=samplerate, blocking=True)
        print("Playback finished.")
    except Exception as e:
        print(f"Failed to play audio: {e}")
        print("Audio saved to disk but could not play it. Ensure you are on a system with audio output.")

async def async_main():
    print("=== Manual Push-to-Talk Test ===")
    
    # Generate a dummy token to test the endpoint
    token = create_access_token({"sub": "testuser"})
    
    # Use the record function
    print("Press and hold 'F9' to speak...")
    audio_bytes = record_on_hotkey(hotkey="f9", max_duration_seconds=10)
    
    if not audio_bytes:
        print("No audio recorded.")
        return
        
    print(f"Recorded {len(audio_bytes)} bytes of audio.")
    
    # Hit local API
    url = "http://localhost:8000/voice/query"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    files = {
        "file": ("test.wav", audio_bytes, "audio/wav")
    }
    
    print("Sending to API...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, files=files)
            
            if response.status_code != 200:
                print(f"API Error ({response.status_code}): {response.text}")
                return
                
            data = response.json()
            print(f"Transcribed Text: {data.get('transcribed_text', '')}")
            print(f"Agent Response: {data.get('agent_response_text', '')}")
            
            response_audio_base64 = data.get('audio_base64', '')
            if response_audio_base64:
                response_audio_bytes = base64.b64decode(response_audio_base64)
                
                # Save response for inspection
                with open("response_test.wav", "wb") as f:
                    f.write(response_audio_bytes)
                print("Saved response to response_test.wav")
                    
                play_audio(response_audio_bytes)
            else:
                print("No audio returned from API.")
            
    except Exception as e:
        print(f"Error calling API: {e}")

def main():
    asyncio.run(async_main())

if __name__ == "__main__":
    main()
