import os
import ssl
from sqlalchemy import Column, BigInteger, String, Integer, select, delete, Boolean
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

raw_url = os.getenv("DATABASE_URL")

if raw_url:
    clean_url = raw_url.split("?")[0].strip()
    if clean_url.startswith("postgres://"):
        DATABASE_URL = clean_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif clean_url.startswith("postgresql://"):
        DATABASE_URL = clean_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    else:
        DATABASE_URL = clean_url
else:
    DATABASE_URL = "sqlite+aiosqlite:///:memory:"

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

engine = create_async_engine(
    DATABASE_URL, 
    echo=False, 
    connect_args={"ssl": ssl_context} if "sqlite" not in DATABASE_URL else {}
)

async_session = async_sessionmaker(engine, expire_on_commit=False)
Base = declarative_base()

class Favorite(Base):
    __tablename__ = "favorites"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, index=True)
    ticker = Column(String)

class UserSetting(Base):
    __tablename__ = "user_settings"
    user_id = Column(BigInteger, primary_key=True)
    is_subscribed = Column(Boolean, default=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created (if not existed)")

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

async def toggle_subscription(user_id: int):
    async with async_session() as session:
        result = await session.execute(select(UserSetting).where(UserSetting.user_id == user_id))
        setting = result.scalar_one_or_none()
        if not setting:
            setting = UserSetting(user_id=user_id, is_subscribed=True)
            session.add(setting)
        else:
            setting.is_subscribed = not setting.is_subscribed
        await session.commit()
        return setting.is_subscribed

async def get_subscription_status(user_id: int) -> bool:
    async with async_session() as session:
        result = await session.execute(select(UserSetting.is_subscribed).where(UserSetting.user_id == user_id))
        status = result.scalar()
        return status if status is not None else False

async def get_all_subscribers():
    async with async_session() as session:
        result = await session.execute(select(UserSetting.user_id).where(UserSetting.is_subscribed == True))
        return result.scalars().all()