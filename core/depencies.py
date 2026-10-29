from typing import Annotated
from redis.asyncio import Redis
from core.database import get_db
from core.security import verify_access_token,verify_refresh_token,give_tokens
from repository.user_repository import UserRepository
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends,HTTPException,Request
from sqlalchemy.ext.asyncio import AsyncSession
from core.redis_config import r
from services.user_service import UserService


oauth2_scheme = OAuth2PasswordBearer(tokenUrl = "users/login")


async def get_redis():
    return r 

async def get_current_user(access_token: Annotated[str, Depends(oauth2_scheme)], session : AsyncSession = Depends(get_db), redis_client : Redis = Depends(get_redis)):
    payload = verify_access_token(access_token)
    jti = payload.get("jti")
    redis_key = f"blacklist:access:{jti}"
    cached_data = await redis_client.get(redis_key)
    
    if not cached_data:
        user_id = payload.get("sub")
        user = await UserRepository(session).get_user_by_id(int(user_id))
    else: 
        raise HTTPException(status_code= 401, detail="This token is used")
    
    return user

async def refresh_tokens(refresh_token : str, session: AsyncSession = Depends(get_db),redis_client : Redis = Depends(get_redis)):
    payload = verify_refresh_token(refresh_token)
    jti = payload.get("jti")
    redis_key = f"blacklist:refresh:{jti}"
    cached_data = await redis_client.get(redis_key)
    
    if not cached_data:
        user_id = payload.get("sub")
        await UserService(session,redis_client).add_refresh_token_to_blacklist(refresh_token)
    else: 
        raise HTTPException(status_code= 401, detail="This token is used")
    
    tokens = give_tokens(user_id)   
    return tokens 
    
async def rate_limiter(request: Request,redis_client : Redis = Depends(get_redis)):
    client_ip = request.client.host
    key = f'request user:{client_ip}'
    current_count = await redis_client.incr(key)
    if current_count == 1:
        await redis_client.expire(key,3600)
    if current_count >= 10:
        raise HTTPException(status_code= 429, detail="Too many requests")
    return current_count

async def get_http_client(request : Request):
    http_client = request.state.client 
    return http_client


