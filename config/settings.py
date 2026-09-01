from pydantic_settings import BaseSettings , SettingsConfigDict


class Settings(BaseSettings):
    DEBUG: bool = True
    DATABASE_URL: str 
    SECRET_KEY: str
    ALGORITHM: str
    EXPIRE_MINUTES: int

    model_config = SettingsConfigDict(env_file=".env")
    
settings = Settings()