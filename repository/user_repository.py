from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select,text,update
from models.user_models import User

class UserRepository():
    def __init__(self,  session: AsyncSession):
        self.session = session
    
    async def add(self,name : str, email: str, hashed_password: str):
        user = User(name = name, email = email, hashed_password = hashed_password)
        self.session.add(user)
        await self.session.flush()
        return user
        
    async def get_user_by_email(self,email):
        query = select(User).where(User.email == email)
        result = await self.session.execute(query)
        user_by_email = result.scalar_one_or_none()
        return user_by_email
    
    async def get_user_by_id(self, id):
        query = select(User).where(User.id == id)
        result = await self.session.execute(query)
        user_by_id = result.scalar_one_or_none()
        return user_by_id
    
    async def get_user_by_email_raw(self, email): 
        raw_user = await self.session.execute(text("Select * from users where email = :email"), {"email" : email})
        raw_user_by_email = raw_user.fetchone()
        return raw_user_by_email 
        
    async def count_users(self):
        raw_count_user = await self.session.execute(text("Select COUNT(*) from users"))
        count_users = raw_count_user.scalar()
        return count_users
    
    async def change_password(self, new_hashed_password, id):
        query = update(User).where(User.id == id).values(hashed_password = new_hashed_password)
        result = await self.session.execute(query)
        
            

