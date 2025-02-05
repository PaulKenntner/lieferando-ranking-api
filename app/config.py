from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings/configuration"""
    DATABASE_URL: str = "postgresql://user:password@db:5432/lanch_db"
    SCRAPING_INTERVAL_MINUTES: int = 60
    BASE_LIEFERANDO_URL: str = "https://www.lieferando.de"
    
    class Config:
        env_file = ".env"

settings = Settings() 