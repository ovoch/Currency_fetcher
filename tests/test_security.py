from unittest.mock import AsyncMock, patch
import pytest
from core.security import give_token, verify_token
from jwt.exceptions import PyJWTError
from fastapi.security import HTTPAuthorizationCredentials
from models.user_models import User
from core.depencies import get_current_user

def test_token():
    assert 5 == int(verify_token(give_token(5)).get("sub"))
    
def test_PyError():
    pytest.raises(PyJWTError, verify_token, token = "asdasd")
    
    
@pytest.mark.asyncio   
async def test_get_current_user():
    token = give_token(100)
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer", 
        credentials= token  
    ) 
    fake_user = User(id=100, name="Ars", email="Ars@test.com", hashed_password="asdasfasd", is_active=True)
    mock = AsyncMock()
    
    
    with patch('core.depencies.UserRepository', autospec=True) as MockClass:
        instance = MockClass.return_value
        instance.get_user_by_id.return_value = fake_user 
        found_user = await get_current_user(credentials, mock)
        
    
    assert found_user is fake_user
    
@pytest.mark.asyncio     
async def test_invalid_token_in_user():
    mock = AsyncMock()
    credentials1 = HTTPAuthorizationCredentials(
        scheme="Bearer", 
        credentials= "asdasd")
    with pytest.raises(PyJWTError):
        await get_current_user(credentials1, mock)
        
    
    
    
        
        