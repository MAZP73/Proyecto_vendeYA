from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    gemini_api_key: str
    host: str = "0.0.0.0"
    port: int = 8001
    ms_post_processing_url: str
    supabase_url: str
    supabase_key: str

    class Config:
        env_file = ".env"

settings = Settings()