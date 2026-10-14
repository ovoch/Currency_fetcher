from pydantic_settings import BaseSettings, SettingsConfigDict

class AuthSettings(BaseSettings):
    SecretKey: str
    Algorithm: str
    AccessTime : int 
    RefreshTime : int
    
    model_config = model_config = SettingsConfigDict(env_file='.env', env_prefix='JWT_', extra='ignore')