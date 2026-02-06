import os
import google.generativeai as genai
from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')

router = Router()

def get_lang_keyboard():
    buttons = [
        [
            InlineKeyboardButton(text="Русский 🇷🇺", callback_data="lang_ru"),
            InlineKeyboardButton(text="English 🇺🇸", callback_data="lang_en")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.message(CommandStart())
async def start_handler(message: types.Message):
    await message.answer(
        "🍽️ **Choose your language / Выберите язык**",
        reply_markup=get_lang_keyboard(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("lang_"))
async def language_callback(callback: CallbackQuery):
    lang = callback.data.split("_")[1]
    
    if lang == "ru":
        text = (
            "👨‍🍳 **Добро пожаловать в AI Chef!**\n\n"
            "Я ваш персональный кулинарный помощник. Я помогу превратить скучный набор продуктов в шедевр.\n\n"
            "**Как пользоваться:**\n"
            "1️⃣ Пришлите список продуктов через запятую (например: *курица, картофель, сыр*).\n"
            "2️⃣ Я предложу несколько пошаговых рецептов.\n"
            "3️⃣ Наслаждайтесь готовкой!\n\n"
            "*Жду ваш список ингредиентов!*"
        )
    else:
        text = (
            "👨‍🍳 **Welcome to AI Chef!**\n\n"
            "I'm your personal culinary assistant. I'll help you turn simple ingredients into a masterpiece.\n\n"
            "**How to use:**\n"
            "1️⃣ Send a list of ingredients (e.g., *chicken, potatoes, cheese*).\n"
            "2️⃣ I'll suggest a few step-by-step recipes.\n"
            "3️⃣ Enjoy your meal!\n\n"
            "*Ready to cook? Send me your list!*"
        )
    
    # Убираем часы ожидания у кнопки и редактируем сообщение
    await callback.answer()
    await callback.message.edit_text(text, parse_mode="Markdown")

@router.message()
async def chef_handler(message: types.Message):
    if not message.text:
        return
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

    prompt = (
        f"You are a world-class chef. Based on these ingredients: {message.text}, "
        "suggest 2 delicious recipes. \n"
        "IMPORTANT: Provide your response in the SAME LANGUAGE as the user used to list the ingredients. "
        "Be concise, professional, and use Markdown for formatting."
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