from pydantic_settings import BaseSettings, SettingsConfigDict

class EmailSettings(BaseSettings):
    Login : str
    Password : str
    SMTP : str
    Port : int
    
    model_config = SettingsConfigDict(env_file='.env',env_prefix='EMAIL_', extra='ignore')
    
em = EmailSettings()