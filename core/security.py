import uuid
import jwt
from pwdlib import PasswordHash
from datetime import datetime, timedelta, timezone
from core.auth_config import AuthSettings
from jwt.exceptions import PyJWTError

password_hash = PasswordHash.recommended()

auth = AuthSettings()

def password_hashed(password: str):
    hash = password_hash.hash(password)
    return hash

def verify_password(plain_password: str,hashed_password: str):
    return password_hash.verify(plain_password, hashed_password)

def give_tokens(id: int):
    refesh_token = jwt.encode(
        {
            "jti" : str(uuid.uuid4()),
            "type": "refresh",
            "sub":str(id),
            "exp": datetime.now(timezone.utc) + timedelta(days = auth.RefreshTime)
        },
        auth.SecretKey,
        auth.Algorithm
    )
    access_token = jwt.encode(
        {
            "jti" : str(uuid.uuid4()),
            "type": "access",
            "sub":str(id),
            "exp": datetime.now(timezone.utc) + timedelta(minutes = auth.AccessTime)
        },
        auth.SecretKey,
        auth.Algorithm)
    token_dict = {
        "access_token" : access_token,
        "refresh_token" : refesh_token,
        "token_type" : "bearer"
    }
    return token_dict

def verify_access_token(acess_token: str):
    payload = jwt.decode(acess_token, auth.SecretKey, algorithms=[auth.Algorithm])
    type = payload.get("type")
    
    if type != "access":
        raise PyJWTError
    
    return payload

def verify_refresh_token(refresh_token: str):
    payload = jwt.decode(refresh_token, auth.SecretKey, algorithms=[auth.Algorithm])
    type = payload.get("type")
    
    if type != "refresh":
        raise PyJWTError
    
    return payload







    
    


            
    
