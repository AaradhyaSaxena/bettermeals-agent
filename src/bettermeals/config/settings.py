from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    groq_api_key: Optional[str] = None
    claude_api_key: Optional[str] = None
    tavily_api_key: Optional[str] = None
    bm_api_base: AnyHttpUrl = "https://api.bettermeals.in"
    env: str = "dev"

    class Config:
        env_file = ".env"

settings = Settings()
