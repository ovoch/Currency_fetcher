from datetime import datetime
import logging
from fastapi import HTTPException
from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from repository.user_repository import UserRepository
from core.security import give_tokens, password_hashed, verify_access_token, verify_password, verify_refresh_token


class UserService():
    
    
    def __init__(self, session : AsyncSession, redis_client : Redis):
        self.session = session
        self.redis_client = redis_client
       
    async def add_access_token_to_blacklist(self,access_token: str):
        now = datetime.now()
        payload = verify_access_token(access_token)
        jti = payload.get("jti")
        experation_time = payload.get("exp")
        token_time_left = now - datetime(experation_time)
        redis_key = f"{jti}"
        cached_data = self.redis_client.get(redis_key)
        if not cached_data:
            await self.redis_client.set(jti, exp = token_time_left)
        else : raise HTTPException(status_code= 401, detail="Token is expired")
        
    async def add_refresh_token_to_blacklist(self,refresh_token: str):
        now = datetime.now()
        payload = verify_refresh_token(refresh_token)
        jti = payload.get("jti")
        experation_time = payload.get("exp")
        token_time_left = now - datetime(experation_time)
        redis_key = f"{jti}"
        cached_data = self.redis_client.get(redis_key)
        if not cached_data:
            await self.redis_client.set(jti, exp = token_time_left)
        else : raise HTTPException(status_code= 401, detail="Token is expired")
        await self.redis_client.set(jti, exp = token_time_left)
        
    async def authenticate_user(self, email : str, password: str):
        user = await UserRepository(self.session).get_user_by_email(email)
    
     # Отсекаем плохой сценарий №1: Юзера нет
        if not user:
            raise HTTPException(status_code=401, detail="Email or password is incorrect")
        
     # Отсекаем плохой сценарий №2: Пароль не совпал
        if not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Email or password is incorrect")
        
     # Сюда код дойдет ТОЛЬКО если всё идеально
        tokens = give_tokens(user.id)
     # По стандарту OAuth2 токен возвращают в виде словаря:
        return tokens
    
    async def create_user(self, name : str, email: str, password: str):
        hashed_password = password_hashed(password)
        user = await UserRepository(self.session).add(name,email,hashed_password)
        await self.session.commit()
        return user
    
    async def count_users(self):
        repo = UserRepository(self.session)
        count = await repo.count_users()
        logging.debug(f"The amount of users is {count}")
        return count
    
    async def change_password(self,password: str, new_password : str, hashed_password: str, user_id):
        if password == new_password:
            raise HTTPException(status_code=400, detail="New password must be new") 
        if not verify_password(password, hashed_password):
            logging.warning("Password is invalid")
            raise HTTPException(status_code= 400, detail="Password is invalid")
        new_hashed_password = password_hashed(new_password)
        await UserRepository(self.session).change_password(new_hashed_password, user_id)
        await self.session.commit()
        logging.debug("Password is changed successfully")
        return {"detail" : "Password is changed"}
    
    
    
        
    
        
    