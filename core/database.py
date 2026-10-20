from sqlalchemy.ext.asyncio import async_sessionmaker,create_async_engine
from sqlalchemy import URL, NullPool
from core.db_config import DataBaseSettings

db = DataBaseSettings()

url_object = URL.create(
        db.DriverDatabase,
        username = db.Username,
        password = db.Password, 
        host = db.Host,
        database = db.NameDatabase,
    )

engine = create_async_engine(url_object, echo=True)
celery_engine = create_async_engine(url_object, echo = True, poolclass=NullPool )

async_session_celery = async_sessionmaker(celery_engine, expire_on_commit= False)
async_session = async_sessionmaker(engine, expire_on_commit=False)
async_session_background = async_sessionmaker(engine,expire_on_commit= True)

async def get_db():
    async with async_session() as session:
        yield session
        
async def get_session_background():
    async with async_session_background() as session:
        yield session