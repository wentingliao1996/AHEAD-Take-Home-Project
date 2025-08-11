from app.db.models import Base
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from .config import settings

DATABASE_URL = (
    f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
    f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
)

engine = create_async_engine(DATABASE_URL, future=True)
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

sync_engine = create_engine(DATABASE_URL)

def create_tables():
    Base.metadata.create_all(bind=sync_engine)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

if __name__ == "__main__":
    create_tables()
    print("創建資料表成功")