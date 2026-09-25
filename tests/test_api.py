import pytest
import os
import httpx
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from fastapi_limiter import FastAPILimiter
import redis.asyncio as redis

from src.api.main import app
from src.database.models import Base
from src.database.session import get_db

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_ats.db"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)

async def override_get_db():
    async with TestSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture(autouse=True)
async def prepare_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    # Mock Redis for FastAPILimiter so tests don't crash without real Redis
    from unittest.mock import AsyncMock
    mock_redis = AsyncMock()
    from fastapi_limiter import FastAPILimiter
    await FastAPILimiter.init(mock_redis)
    
    from fastapi_cache import FastAPICache
    from fastapi_cache.backends.inmemory import InMemoryBackend
    FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")
    
    yield
    
@pytest_asyncio.fixture
async def client():
    from httpx import ASGITransport
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_auth_and_job_creation(client):
    # 1. Create tenant
    res = await client.post("/tenants/", json={"name": "Acme Corp", "password": "securepassword"})
    assert res.status_code == 200
    tenant = res.json()
    assert tenant["name"] == "Acme Corp"
    tenant_id = tenant["id"]
    
    # 2. Login
    res = await client.post("/login", data={"username": "admin@acmecorp.com", "password": "securepassword"})
    assert res.status_code == 200
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Create job securely
    res = await client.post("/jobs/", json={
        "title": "Software Engineer",
        "raw_text": "We need a Python developer with 3 years of experience and AWS skills."
    }, headers=headers)
    assert res.status_code == 200
    job = res.json()
    assert job["title"] == "Software Engineer"
    assert job["tenant_id"] == tenant_id
    assert "skills" in job["parsed_json"]
    
@pytest.mark.asyncio
async def test_multi_tenant_isolation(client):
    # Create two tenants
    t1 = await client.post("/tenants/", json={"name": "Org 1", "password": "p1"})
    t2 = await client.post("/tenants/", json={"name": "Org 2", "password": "p2"})
    t1_id = t1.json()["id"]
    
    # Login as T1 and T2
    t1_token = (await client.post("/login", data={"username": "admin@org1.com", "password": "p1"})).json()["access_token"]
    t2_token = (await client.post("/login", data={"username": "admin@org2.com", "password": "p2"})).json()["access_token"]
    
    # T1 creates a job
    j1 = await client.post(f"/jobs/", json={
        "title": "T1 Job", "raw_text": "Job 1"
    }, headers={"Authorization": f"Bearer {t1_token}"})
    j1_id = j1.json()["id"]
    
    # T2 tries to access T1's job - it should fail because route verifies job belongs to token's tenant
    res = await client.get(f"/jobs/{j1_id}/candidates/", headers={"Authorization": f"Bearer {t2_token}"})
    assert res.status_code == 404
