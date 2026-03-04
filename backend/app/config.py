# backend/app/config.py
from pydantic_settings import BaseSettings
from typing import List
import json


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./tap_split.db"

    # OCR
    TESSDATA_PREFIX: str = "/usr/share/tesseract-ocr/4.00/tessdata"

    # Security
    CORS_ORIGINS: str = '["*"]'

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = True

    @property
    def cors_origins_list(self) -> List[str]:
        try:
            return json.loads(self.CORS_ORIGINS)
        except:
            return ["*"]

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
