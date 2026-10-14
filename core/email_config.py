from pydantic_settings import BaseSettings, SettingsConfigDict

class EmailSettings(BaseSettings):
    Login : str
    Password : str
    
    model_config = SettingsConfigDict(env_file='.env',env_prefix='EMAIL_', extra='ignore')
    
em = EmailSettings()