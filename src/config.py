from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
import os

class Settings(BaseSettings):
    gemini_api_key: str = Field(default="", env="GEMINI_API_KEY")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Allows falling back to .env file if available, but isn't strictly required
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

# Load settings singleton
settings = Settings()
