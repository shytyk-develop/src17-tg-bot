import os
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Update
from aiogram.webhook.aiohttp_server import TokenBasedRequestHandler
from bot_instance import get_dispatcher

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = get_dispatcher()

async def handler(request):
    if request.method == "POST":
        update = Update.model_validate(await request.json(), context={"bot": bot})
        await dp.feed_update(bot, update)
        return {"statusCode": 200, "body": "ok"}
    return {"statusCode": 200, "body": "Only POST allowed"}

async def main(request):
    return await handler(request)