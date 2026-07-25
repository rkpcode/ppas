from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./pharmacy.db"
    JWT_SECRET_KEY: str
    ANTHROPIC_API_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 480
    
    # NVIDIA API Config
    NVIDIA_API_KEY: str = ""
    NVIDIA_AGENT_MODEL: str = "deepseek-ai/deepseek-v4-flash"
    NVIDIA_FAST_MODEL: str = "meta/llama-3.1-8b-instruct"
    NVIDIA_REASONING_MODEL: str = "nvidia/nemotron-3-ultra-550b-a55b"
    NVIDIA_TTS_MODEL: str = "resembleai/chatterbox-multilingual-tts"
    
    # Voice layer config (Sarvam for STT only)
    SARVAM_API_KEY: str = ""
    SARVAM_STT_MODEL: str = "saaras:v3"
    PUSH_TO_TALK_HOTKEY: str = "f9"
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
