from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import CommandStart

router = Router()

@router.message(CommandStart())
async def start_handler(message: types.Message):
    await message.answer("Привет! Я работаю на Vercel через Webhooks! 🚀")

def get_dispatcher():
    dp = Dispatcher()
    dp.include_router(router)
    return dp