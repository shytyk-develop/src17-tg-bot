import asyncio
import os
from fastapi import FastAPI, Request
from aiogram import Bot, types
from aiogram.types import Update
from bot_instance import get_dispatcher 

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)

dp = get_dispatcher()

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
    return {"status": "Bot is running with AI Chef logic!"}