from pydantic import BaseModel,ConfigDict, EmailStr, Field

class UserCreate(BaseModel):
    name : str = Field(min_length = 1)
    email : EmailStr
    password : str
    
    model_config = ConfigDict(from_attributes=True)

class UserResponse(BaseModel):
    id : int
    name : str
    email : EmailStr
    is_active : bool
    
    model_config = ConfigDict(from_attributes=True)
    
class UserLogin(BaseModel):
    email : EmailStr
    password : str
    
    model_config = ConfigDict(from_attributes=True)
    
class UserChangePassword(BaseModel):
    password : str
    new_password : str
    
    model_config = ConfigDict(from_attributes=True)
    
class UserShort(BaseModel):
    email : EmailStr
    
class RefreshToken(BaseModel):
    refresh_token : str
    
    

