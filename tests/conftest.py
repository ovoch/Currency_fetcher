import httpx
import pytest
import redis.asyncio as redis
from sqlalchemy import URL, NullPool
from core.database import db,get_db
from sqlalchemy.ext.asyncio import async_sessionmaker,create_async_engine
from core.depencies import get_http_client, get_redis
from models.base_models import Base
from main import app
from core.redis_config import rd



url_object = URL.create(
        db.DriverDatabase,
        username = db.Username,
        password = db.Password, 
        host = db.HostTest,
        database = db.NameDatabaseTest
    )

test_engine = create_async_engine(url_object, poolclass = NullPool)
async_session_test = async_sessionmaker(test_engine, expire_on_commit = False)

@pytest.fixture(scope="session", autouse=True)
async def setup_test_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    yield
        
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def handler(request: httpx.Request):
    if request.url.path.endswith("/latest") and request.url.params.get("base") == "USD":
        return httpx.Response(
            200,json={"base": "USD", "rates": {"EUR": "1.254"}}, request= request
        )
    return httpx.Response(404, json = {"error":"Invalid request"}, request= request)
    
    
@pytest.fixture(scope="function")
async def db_session():

        
    connection = await test_engine.connect()
    transaction = await connection.begin()
    session = async_session_test(bind = connection)
        
    yield session
        
    await transaction.rollback()
    await connection.close()
    
@pytest.fixture(scope = "function")
async def redis_test():
    red = redis.Redis(host= rd.HostTest, port=6379, db=1, decode_responses=True, password= rd.Password)
    yield red
    
    await red.flushdb()
    await red.close()
        

@pytest.fixture(scope = "function")
async def py_clients(db_session,redis_test):
        
    async def override_get_db():
        yield db_session
        
    async def override_get_redis():
        yield redis_test
    
    async def override_get_http_client():
        transport_http = httpx.MockTransport(handler)
        client = httpx.AsyncClient(transport=transport_http)
        yield client
            
    transport = httpx.ASGITransport(app=app)
    
    
    app.dependency_overrides[get_redis] = override_get_redis    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_http_client] = override_get_http_client
        
    async with (httpx.AsyncClient(transport=transport,base_url="http://test") as client,):
        yield client
           
    app.dependency_overrides.clear()