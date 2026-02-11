import os
import ssl
from sqlalchemy import Column, BigInteger, String, Integer, select, delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

raw_url = os.getenv("DATABASE_URL")

DATABASE_URL = ""
connect_args = {}

if raw_url:
    if raw_url.startswith("postgres://"):
        url_with_driver = raw_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif raw_url.startswith("postgresql://"):
        url_with_driver = raw_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    else:
        url_with_driver = raw_url

    if "?" in url_with_driver:
        DATABASE_URL = url_with_driver.split("?")[0]
    else:
        DATABASE_URL = url_with_driver

    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    connect_args = {"ssl": ssl_context}
    
else:
    DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    DATABASE_URL, 
    echo=False,
    connect_args=connect_args
)

async_session = async_sessionmaker(engine, expire_on_commit=False)

Base = declarative_base()

class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, index=True)
    ticker = Column(String)

async def init_db():
    if engine:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

async def add_favorite(user_id: int, ticker: str):
    async with async_session() as session:
        result = await session.execute(
            select(Favorite).where(Favorite.user_id == user_id, Favorite.ticker == ticker)
        )
        if result.scalar():
            return False 

        new_fav = Favorite(user_id=user_id, ticker=ticker)
        session.add(new_fav)
        await session.commit()
        return True

async def remove_favorite(user_id: int, ticker: str):
    async with async_session() as session:
        await session.execute(
            delete(Favorite).where(Favorite.user_id == user_id, Favorite.ticker == ticker)
        )
        await session.commit()

async def get_user_favorites(user_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(Favorite.ticker).where(Favorite.user_id == user_id)
        )
        return result.scalars().all()