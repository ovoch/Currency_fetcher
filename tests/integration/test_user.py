from sqlalchemy import text
from models.user_models import User
from core.security import password_hashed,give_tokens
from services.user_service import UserService

async def test_register_success(py_clients, db_session):
    user = {
        "name" : "Ars",
        "email" : "lol@test.com",
        "password" : "123456"
    }
    user_answer = await py_clients.post("/users",json = user)
    assert user_answer.status_code == 200
    password_from_db = await db_session.execute(text("Select hashed_password from users where email = 'lol@test.com'"))
    hash_password = password_from_db.scalar_one_or_none()
    user_dict = user_answer.json()
    assert "password" not in user_dict
    assert "hashed_password" not in user_dict
    assert hash_password is not None
    assert user["password"] != hash_password
    assert user_dict["name"] == user["name"]
    assert user_dict["email"] == user["email"]
    assert isinstance(user_dict["id"],int)

async def test_duplicate_email(py_clients,db_session):
    user_first = User(
        name = "Ars",
        email = "lol@test.com",
        hashed_password = "123456",
        is_active = True)
    
    user_second = {
        "name" : "LOL",
        "email" : "lol@test.com",
        "password" : "123456"
    }
    db_session.add(user_first)
    await db_session.flush()
    user_answer = await py_clients.post("/users",json = user_second)
    assert user_answer.status_code == 409
    assert user_answer.json()["detail"] == "User already exists"

async def test_register_fail(py_clients):
    user_first = {
        "name" : None,
        "email" : "lol@test.com",
        "password" : "123456"
    }
    user_second = {
        "name" : "LOL",
        "email" : "no-email",
        "password" : "123456"
    }
    user_answer_first =  await py_clients.post("/users",json = user_first)
    user_answer_second =  await py_clients.post("/users",json = user_second)
    assert user_answer_second.status_code == 422 
    assert user_answer_first.status_code == 422
    user_dict_first = user_answer_first.json()
    user_dict_second = user_answer_second.json()
    assert user_dict_first["detail"][0]["loc"][-1] == "name"
    assert user_dict_second["detail"][-1]["loc"][-1] == "email"
    
async def test_login_success(py_clients,db_session):
    hash_password = password_hashed("123456")
    
    user = User(
        name = "Ars",
        email = "lol@test.com",
        hashed_password = hash_password,
        is_active = True)
    
    db_session.add(user)
    await db_session.flush()
    
    user_form = {
        "username" : "lol@test.com",
        "password" : "123456" 
    }
    
    user_answer = await py_clients.post("/users/login", data = user_form)
    user_dict = user_answer.json()
    assert user_answer.status_code == 200
    assert "access_token" in user_dict
    assert "refresh_token" in user_dict
    assert "token_type" in user_dict
    
async def test_login_fail(py_clients,db_session):
    hash_password = password_hashed("123456")
    
    user = User(
        name = "Ars",
        email = "lol@test.com",
        hashed_password = hash_password,
        is_active = True)
    
    db_session.add(user)
    await db_session.flush()
    
    user_no_username = {
        "username" : "",
        "password" : "123456" 
    }
    
    user_invalid_password = {
        "username" : "lol@test.com",
        "password" : "1234" 
    }
    user_invalid_username = {
        "username" : "asdasd@test.com",
        "password" : "123456" 
    }
    
    user_no_username_answer = await py_clients.post("/users/login", data = user_no_username)
    user_no_username_dict = user_no_username_answer.json()
    assert user_no_username_answer.status_code == 422
    assert user_no_username_dict["detail"][0]["loc"][-1] == "username"
    
    user_invalid_password_answer = await py_clients.post("/users/login", data = user_invalid_password)
    user_invalid_password_dict = user_invalid_password_answer.json()
    assert user_invalid_password_answer.status_code == 401
    assert user_invalid_password_dict["detail"] == "Email or password is incorrect"
    
    user_invalid_username_answer = await py_clients.post("/users/login", data = user_invalid_username)
    user_invalid_username_dict = user_invalid_username_answer.json()
    assert user_invalid_username_answer.status_code == 401
    assert user_invalid_username_dict["detail"] == "Email or password is incorrect"
    
async def test_get_current_user_success(py_clients,db_session):
    hash_password_in = password_hashed("123456")
    
    user = User(
        name = "Ars",
        email = "lol@test.com",
        hashed_password = hash_password_in,
        is_active = True) 
    
    db_session.add(user)
    await db_session.flush()
    
    tokens = give_tokens(user.id)
    access_token = tokens["access_token"]
    
    user_answer = await py_clients.get("/users/me", headers = {"Authorization": f"Bearer {access_token}"})
    assert user_answer.status_code == 200
    user_dict = user_answer.json()
    assert "password" not in user_dict
    assert "hashed_password" not in user_dict
    assert user_dict["name"] == user.name
    assert user_dict["email"] == user.email
    assert isinstance(user_dict["id"],int)
    
async def test_get_current_user_fail(py_clients,db_session,redis_test):
    hash_password_in = password_hashed("123456")
    
    user = User(
        name = "Ars",
        email = "lol@test.com",
        hashed_password = hash_password_in,
        is_active = True) 
    
    db_session.add(user)
    await db_session.flush()
    
    tokens = give_tokens(user.id)
    access_token = tokens["access_token"]
    access_token_invalid = "asdasdw"
    
    
    user_answer_invalid_token = await py_clients.get("/users/me", headers = {"Authorization": f"Bearer {access_token_invalid}"})
    assert user_answer_invalid_token.status_code == 401
    
    user_answer_no_token = await py_clients.get("/users/me")
    assert user_answer_no_token.status_code == 401
    user_answer_no_token_dict = user_answer_no_token.json()
    assert  user_answer_no_token_dict["detail"] == "Not authenticated"
    
    await UserService(db_session,redis_test).add_access_token_to_blacklist(access_token)
    user_answer = await py_clients.get("/users/me", headers = {"Authorization": f"Bearer {access_token}"})
    assert user_answer.status_code == 401
    user_dict = user_answer.json()
    assert user_dict["detail"] == "This token is used"
    
async def test_logout_success(py_clients,db_session):
    hash_password_in = password_hashed("123456")
    
    user = User(
        name = "Ars",
        email = "lol@test.com",
        hashed_password = hash_password_in,
        is_active = True) 
    
    db_session.add(user)
    await db_session.flush()
    
    tokens_in = give_tokens(user.id)
    refresh_token_in = tokens_in["refresh_token"]
    access_token_in = tokens_in["access_token"]
    refresh_token_dict = {"refresh_token" : f"{refresh_token_in}"}
    
    answer = await py_clients.post("/users/logout", json= refresh_token_dict, headers = {"Authorization": f"Bearer {access_token_in}"})
    assert answer.status_code == 200
    
    answer_out_access = await py_clients.get("/users/me",headers = {"Authorization": f"Bearer {access_token_in}"})
    assert answer_out_access.status_code == 401
    dict_out_access = answer_out_access.json()
    assert dict_out_access["detail"] == "This token is used"

    answer_out_refresh = await py_clients.post("/users/refresh/tokens",json = refresh_token_dict)
    assert answer_out_refresh.status_code == 401
    dict_out_refresh = answer_out_refresh.json()
    assert dict_out_refresh["detail"] == "This token is used"

async def test_logout_fail(py_clients):    
    
    tokens_in = give_tokens(1)
    access_token_in = tokens_in["access_token"]
    
    answer_invalid_access = await py_clients.post("/users/logout", headers = {"Authorization": ""})
    assert answer_invalid_access.status_code == 401
    
    answer_invalid_refresh = await py_clients.post("/users/logout", json = "ajsdnlaskdnaksjdbkasjd",headers = {"Authorization": f"Bearer {access_token_in}"})
    assert answer_invalid_refresh.status_code == 422
    
async def test_refresh_tokens_access(py_clients):
    
    tokens_in = give_tokens(1)
    refresh_token_in = tokens_in["refresh_token"]
    refresh_token_dict = {"refresh_token" : f"{refresh_token_in}"}
    
    answer = await py_clients.post("/users/refresh/tokens", json = refresh_token_dict)
    assert answer.status_code == 200
    answer_dict = answer.json()
    
    assert "access_token" in answer_dict
    assert "refresh_token" in answer_dict
    assert "token_type" in answer_dict
    assert answer_dict["refresh_token"] != refresh_token_in
    
    answer_old_refresh_blacklisted = await py_clients.post("/users/refresh/tokens", json = refresh_token_dict)
    
    assert answer_old_refresh_blacklisted.status_code == 401
    answer_old_refresh_blacklisted_dict = answer_old_refresh_blacklisted.json()
    assert answer_old_refresh_blacklisted_dict["detail"] == "This token is used"
    