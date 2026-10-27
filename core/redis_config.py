from pydantic_settings import BaseSettings, SettingsConfigDict
import redis.asyncio as redis
from core.database import db

class Redis_Settings(BaseSettings):
    Password: str
    Host : str
    HostTest : str
        
    model_config = SettingsConfigDict(env_file = ".env", env_prefix="REDIS_", extra ="ignore")
    
rd = Redis_Settings()       
r = redis.Redis(host= rd.Host, port=6379, db=0, decode_responses=True, password= rd.Password)