from sqlalchemy import text
from models.user_models import User

async def test_register_success(py_clients, db_session):
    user = {
        "name" : "Ars",
        "email" : "lol@test.com",
        "password" : "123456"
    }
    user_answer = await py_clients.post("/users/",json = user)
    assert user_answer.status_code == 201
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
    user_answer = await py_clients.post("/users/",json = user_second)
    assert user_answer.status_code == 409
    assert user_answer.json()["detail"] == "User already exists"

async def test_register_fail(py_clients):
    user_first = {
        "name" : "",
        "email" : "lol@test.com",
        "password" : "123456"
    }
    user_second = {
        "name" : "LOL",
        "email" : "no-email",
        "password" : "123456"
    }
    user_answer_first =  await py_clients.post("/users/",json = user_first)
    user_answer_second =  await py_clients.post("/users/",json = user_second)
    assert user_answer_second.status_code == 422 
    assert user_answer_first.status_code == 422
    user_dict_first = user_answer_first.json()
    user_dict_second = user_answer_second.json()
    assert user_dict_first["detail"][0]["loc"][-1] == "name"
    assert user_dict_second["detail"][-1]["loc"][-1] == "email"