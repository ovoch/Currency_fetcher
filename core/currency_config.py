from pydantic_settings import BaseSettings, SettingsConfigDict

class Currency_Settings(BaseSettings):
    URL: str
    
    model_config = SettingsConfigDict(env_file='.env', env_prefix='CUR_', extra='ignore')