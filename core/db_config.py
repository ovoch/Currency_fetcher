from pydantic_settings import BaseSettings, SettingsConfigDict

class DataBaseSettings(BaseSettings):
    DriverDatabase: str
    Username: str
    Password: str
    Host: str
    NameDatabase: str 
    
    model_config = SettingsConfigDict(env_file='.env',env_prefix='DB_', extra='ignore')