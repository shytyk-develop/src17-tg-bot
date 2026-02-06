import os
import google.generativeai as genai
from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import CommandStart

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')

router = Router()

@router.message(CommandStart())
async def start_handler(message: types.Message):
    await message.answer(
        "Hi! I'm your AI Chef. 👨‍🍳\n\n"
        "Just send me a list of ingredients separated by commas (e.g., chicken, potatoes, onion)," 
        "and I’ll suggest something quick and delicious you can whip up!"
    )

@router.message()
async def chef_handler(message: types.Message):
    if not message.text:
        return

    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

    prompt = (
    f"You are an experienced executive chef. You have been given the following list of ingredients: {message.text}. "
    "Suggest 2-3 dish options. For each dish, provide:\n"
    "1. Name of the dish.\n"
    "2. Estimated cooking time.\n"
    "3. A brief step-by-step recipe.\n"
    "Use only these ingredients + basic staples (salt, oil, water). If something critical is missing, please point it out politely."
    )
    try:
        response = model.generate_content(prompt)
        
        await message.answer(response.text, parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"Sorry, our chef is not available: {e}")


def get_dispatcher():
    dp = Dispatcher()
    dp.include_router(router)
    return dp