from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    groq_api_key: Optional[str] = None
    claude_api_key: Optional[str] = None
    tavily_api_key: Optional[str] = None
    athena_api_base: AnyHttpUrl = "https://api.bettermeals.in"
    bm_backend_api_base: AnyHttpUrl = "http://staging-bm.eba-n3mspgd3.ap-south-1.elasticbeanstalk.com/"
    env: str = "dev"

    class Config:
        env_file = ".env"

settings = Settings()
