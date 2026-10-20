import jwt
import pytest
from core.security import password_hashed,verify_password,give_tokens,verify_access_token,verify_refresh_token
from jwt.exceptions import PyJWTError

def test_hash_password_success():
    hash = password_hashed("kek")
    assert "kek" != hash
    assert True == verify_password("kek",hash)
   
def test_hash_password_fail():
    hash = password_hashed("kek")
    assert False == verify_password("lol",hash)
    
    
def test_generate_token_data():
    token = give_tokens(1).get("access_token")
    token_ref = give_tokens(1).get("refresh_token")
    payload_access = verify_access_token(token)
    payload_refresh = verify_refresh_token(token_ref)
    assert "1" == payload_access.get("sub")
    assert "1" == payload_refresh.get("sub")
    assert True == "jti" in payload_access
    assert True == "exp" in payload_access
    assert True == "jti" in payload_refresh
    assert True == "exp" in payload_refresh
    assert "access" == payload_access.get("type")
    assert "refresh" == payload_refresh.get("type")
    
def test_verify_tokens_success():
    token = give_tokens(1).get("access_token")
    token_ref = give_tokens(1).get("refresh_token")
    assert "access" == verify_access_token(token).get("type")
    assert "refresh" == verify_refresh_token(token_ref).get("type")
    
def test_verify_refresh_to_access_token_fail():
    token = give_tokens(1).get("refresh_token")
    with pytest.raises(PyJWTError):
        verify_access_token(token)
        
def test_verify_access_to_refresh_token_fail():
    token = give_tokens(1).get("access_token")
    with pytest.raises(PyJWTError):
        verify_refresh_token(token)
