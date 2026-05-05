import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Load .env file explicitly
load_dotenv()

class AISettings(BaseSettings):
    anthropic_api_key: Optional[str] = None
    mistral_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    model_name: str = "gpt-4o" # Default to GPT-4o if OpenAI is used
    temperature: float = 0.7

class VoiceSettings(BaseSettings):
    elevenlabs_api_key: Optional[str] = None
    pvporcupine_api_key: Optional[str] = None
    wake_word: str = "kolimarii"

class SystemSettings(BaseSettings):
    log_level: str = "INFO"
    log_file: str = "logs/kolimarii.log"
    chroma_db_path: str = "./memory_db"
    adb_path: str = "adb"
    tesseract_cmd: Optional[str] = None

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    
    ai: AISettings = AISettings()
    voice: VoiceSettings = VoiceSettings()
    system: SystemSettings = SystemSettings()

# Global settings instance
settings = Settings()

def get_settings():
    """Returns the global settings instance."""
    return settings
