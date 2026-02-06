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
        f"You are a chef. Based on: {message.text}, suggest 2 quick recipes. "
        "Be concise and clear. Format with Markdown."
    )
    
    try:
        response = model.generate_content(prompt)
        text = response.text
        if len(text) > 4000:
            text = text[:4000] + "\n\n...(truncated due to length)"   
        await message.answer(text, parse_mode="Markdown")
    except Exception as e:
        error_msg = str(e)[:100]
        await message.answer(f"Chef error: {error_msg}")


def get_dispatcher():
    dp = Dispatcher()
    dp.include_router(router)
    return dp