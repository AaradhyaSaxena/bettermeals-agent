from pydantic import BaseSettings, AnyHttpUrl

class Settings(BaseSettings):
    groq_api_key: str
    bm_api_base: AnyHttpUrl = "https://api.bettermeals.in"
    env: str = "dev"

    class Config:
        env_file = ".env"

settings = Settings()
