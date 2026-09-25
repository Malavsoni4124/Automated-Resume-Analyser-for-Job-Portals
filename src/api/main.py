from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import redis.asyncio as redis
from fastapi_limiter import FastAPILimiter
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
import os

from src.database.session import engine
from src.database.models import Base
from src.api.routes import router as api_router
from src.api.chat import router as chat_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB (in development only - Alembic handles production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    # Initialize Redis for caching and rate limiting
    redis_client = None
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        redis_client = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
        await FastAPILimiter.init(redis_client)
        FastAPICache.init(RedisBackend(redis_client), prefix="fastapi-cache")
    except Exception as e:
        print(f"Redis not available, continuing without caching: {e}")
        redis_client = None
    
    yield
    
    if redis_client:
        await redis_client.close()

app = FastAPI(
    title="Automated Resume Analyzer API",
    description="Core engine for multi-tenant Applicant Tracking System",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.include_router(chat_router)

@app.get("/health")
def health_check():
    return {"status": "ok"}
