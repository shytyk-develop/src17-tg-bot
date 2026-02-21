import os
import asyncio
import yfinance as yf
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from aiogram import Bot, types
from aiogram.types import Update
from bot_instance import get_dispatcher, fetch_price
from database import init_db, get_all_subscribers, get_user_favorites

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

@app.get("/api/cron/broadcast")
async def broadcast_handler(request: Request):
    subscribers = await get_all_subscribers()
    for user_id in subscribers:
        favs = await get_user_favorites(user_id)
        if not favs: continue
        
        text = "🔔 Daily Notifications\n\n"
        for t in favs:
            price, curr = await asyncio.to_thread(fetch_price, t)
            text += f"🔹 {t}: `{price} {curr}`\n"
        
        try:
            await bot.send_message(user_id, text, parse_mode="Markdown")
        except Exception:
            pass
    return {"status": "done"}