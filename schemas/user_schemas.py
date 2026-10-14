from pydantic import BaseModel,ConfigDict

class UserCreate(BaseModel):
    name : str
    email : str
    password : str
    
    model_config = ConfigDict(from_attributes=True)

class UserResponse(BaseModel):
    id : int
    name : str
    email : str
    is_active : bool
    
    model_config = ConfigDict(from_attributes=True)
    
class UserLogin(BaseModel):
    email : str
    password : str
    
    model_config = ConfigDict(from_attributes=True)
    
class UserChangePassword(BaseModel):
    password : str
    new_password : str
    
    model_config = ConfigDict(from_attributes=True)
    
class UserShort(BaseModel):
    email : str
    
class RefreshToken(BaseModel):
    refresh_token : str
    
    

