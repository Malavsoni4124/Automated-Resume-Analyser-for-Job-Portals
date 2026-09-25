import asyncio
import os
import sys

# Ensure project root is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.database.session import async_session, engine
from src.database.models import Base, Tenant, Job
from src.api.auth import get_password_hash

async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        # Check if tenant 1 exists
        from sqlalchemy import select
        result = await db.execute(select(Tenant).where(Tenant.id == 1))
        existing_tenant = result.scalar_one_or_none()

        if not existing_tenant:
            tenant = Tenant(
                id=1,
                name="Demo Organization",
                hashed_password=get_password_hash("admin123")
            )
            db.add(tenant)
            await db.commit()
            print("Created Tenant ID 1 with password 'admin123'")
        else:
            print("Tenant ID 1 already exists.")

        # Check if sample job exists
        job_res = await db.execute(select(Job).where(Job.tenant_id == 1))
        existing_job = job_res.scalars().first()

        if not existing_job:
            sample_jd = (
                "We are seeking a Senior Python & AI Software Engineer with experience in FastAPI, "
                "PyTorch, Transformers, PostgreSQL, Docker, and React. Responsibilities include building ATS features, "
                "optimizing NLP pipelines, and scaling microservices."
            )
            job = Job(
                id=1,
                tenant_id=1,
                title="Senior Python & AI Engineer",
                raw_text=sample_jd,
                parsed_json={
                    "title": "Senior Python & AI Engineer",
                    "required_skills": ["Python", "FastAPI", "PyTorch", "Docker", "PostgreSQL", "React"],
                    "experience_years": 4
                }
            )
            db.add(job)
            await db.commit()
            print("Created Sample Job ID 1: Senior Python & AI Engineer")
        else:
            print("Sample Job already exists.")

if __name__ == "__main__":
    asyncio.run(seed())
