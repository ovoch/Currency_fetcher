import decimal
import json
from sqlalchemy import select
from core.security import give_tokens, password_hashed
from models.currency_models import ExchangeRate
from models.user_models import User

async def test_fetch_currency_success(py_clients,redis_test,db_session):
    
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
    
    currencies_in = {"base" : "USD", "target": "EUR"}
    
    answer = await py_clients.post("/currency", headers = {"Authorization": f"Bearer {access_token}"}, json = currencies_in)
    assert answer.status_code == 200
    
    answer_dict = answer.json()
    assert "base" in answer_dict
    assert answer_dict["base"] == "USD"
    assert "rates" in answer_dict
    assert "EUR" in answer_dict["rates"]
    assert answer_dict["rates"]["EUR"] == "1.254"
    

    redis_cache = await redis_test.get("base:USD:target:EUR")
    assert redis_cache is not None

    cached_dict = json.loads(redis_cache)
    assert cached_dict["base"] == "USD"
    assert cached_dict["rates"]["EUR"] == "1.254"
    
    query = select(ExchangeRate).where(ExchangeRate.user_id == user.id)
    result = await db_session.execute(query)
    rate_db =result.scalar_one_or_none()
    
    assert rate_db is not None
    assert rate_db.base_currency == "USD"
    assert rate_db.target_currency == "EUR"
    assert rate_db.currency_rate == decimal.Decimal("1.254")