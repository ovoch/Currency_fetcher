from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from core.depencies import get_current_user, refresh_tokens
from models.user_models import User
from schemas.user_schemas import UserCreate,UserResponse,UserChangePassword,RefreshToken
from repository.user_repository import UserRepository
from fastapi import APIRouter,Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from services.user_service import UserService
from core.redis_config import r 


router = APIRouter(prefix = "/users", tags = ["Users"]) 
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.post("", response_model=UserResponse)
async def create_user(user_in : UserCreate, session: AsyncSession = Depends(get_db)):
    user = await UserService(session,r).create_user(user_in.name, user_in.email, user_in.password)
    return user

@router.post("/login")
async def verify_user(form_data : OAuth2PasswordRequestForm = Depends(), session : AsyncSession = Depends(get_db)):
    tokens = await UserService(session,r).authenticate_user(form_data.username, form_data.password)
    return tokens

@router.get("/me", response_model= UserResponse)
async def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/logout")
async def logout_user(access_token: str, session : AsyncSession = Depends(get_db)):
    await UserService(session,r).add_access_token_to_blacklist(access_token)
    
@router.post("refresh/tokens")
async def refresh_token(refresh_token: RefreshToken, session : AsyncSession = Depends(get_db),):
    tokens = await refresh_tokens(refresh_token.refresh_token,session)
    return tokens
    

@router.get("/count_users")
async def count_users(session: AsyncSession = Depends(get_db)):
    count = await UserService(session,r).count_users()
    return count

@router.get("/{email}", response_model= UserResponse)
async def get_user_by_email(email: str,session : AsyncSession = Depends(get_db)):
    user = await UserRepository(session).get_user_by_email(email)
    return user

@router.patch("/me/change_password")
async def change_password(passwords : UserChangePassword,current_user : User = Depends(get_current_user),session : AsyncSession = Depends(get_db)):
    await UserService(session,r).change_password(passwords.password, passwords.new_password, current_user.hashed_password, current_user.id)



    
    
    