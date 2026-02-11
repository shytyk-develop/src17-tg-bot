import os
import yfinance as yf
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from aiogram import Bot, types
from aiogram.types import Update
from bot_instance import get_dispatcher
from database import init_db

try:
    yf.set_tz_cache_location("/tmp")
except Exception:
    pass

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = get_dispatcher()

db_initialized = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_initialized
    try:
        await init_db()
        db_initialized = True
        print("Database initialized in lifespan")
    except Exception as e:
        print(f"Lifespan init error: {e}")
    yield

app = FastAPI(lifespan=lifespan)

@app.post("/")
async def feed_update(request: Request):
    global db_initialized
    
    if not db_initialized:
        try:
            await init_db()
            db_initialized = True
        except Exception as e:
            print(f"Lazy init error: {e}")

    try:
        json_str = await request.json()
        update = Update.model_validate(json_str, context={"bot": bot})
        await dp.feed_update(bot, update)
    except Exception as e:
        print(f"Update error: {e}")
    return {"ok": True}

@app.get("/")
async def index():
    return {"status": "Active", "db": "Initialized" if db_initialized else "Pending"}