import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
import sys
import os

# Add the root directory to sys.path so we can import src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.models import Base, Tenant, User
from src.api.auth import get_password_hash
from src.database.session import async_session

DATABASE_URL = "sqlite+aiosqlite:///./ats.db"
engine = create_async_engine(DATABASE_URL, echo=True)

async def migrate():
    async with engine.begin() as conn:
        print("Dropping tables...")
        await conn.run_sync(Base.metadata.drop_all)
        print("Creating tables...")
        await conn.run_sync(Base.metadata.create_all)
        
    print("Creating default tenant and admin user...")
    async with async_session() as session:
        default_tenant = Tenant(name="Aero Corp")
        session.add(default_tenant)
        await session.commit()
        await session.refresh(default_tenant)
        
        admin_user = User(
            tenant_id=default_tenant.id,
            email="admin@aerocorp.com",
            name="Admin User",
            hashed_password=get_password_hash("password123"),
            role="admin"
        )
        recruiter_user = User(
            tenant_id=default_tenant.id,
            email="recruiter@aerocorp.com",
            name="Recruiter",
            hashed_password=get_password_hash("password123"),
            role="recruiter"
        )
        session.add_all([admin_user, recruiter_user])
        await session.commit()
        
    print("Migration complete!")

if __name__ == "__main__":
    asyncio.run(migrate())
