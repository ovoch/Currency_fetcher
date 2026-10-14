from pydantic_settings import BaseSettings, SettingsConfigDict

class CelerySettings(BaseSettings):
    Backend : str
    Brocker : str
        
    model_config = SettingsConfigDict(env_file = ".env", env_prefix="CELERY_", extra ="ignore")
    
cel = CelerySettings()