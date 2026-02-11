import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from aiogram import Bot, types
from aiogram.types import Update
from bot_instance import get_dispatcher
from database import init_db

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)

dp = get_dispatcher()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI()

@app.post("/")
async def feed_update(request: Request):
    try:
        json_str = await request.json()
        update = Update.model_validate(json_str, context={"bot": bot})
        await dp.feed_update(bot, update)
    except Exception as e:
        print(f"Error: {e}")
    return {"ok": True}

@app.get("/")
async def index():
    return {"status": "Bot is running with Stock Ticker logic!"}