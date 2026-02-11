import asyncio
import logging
import yfinance as yf
from yfinance import ticker
from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

router = Router()

def get_main_keyboard():
    buttons = [
        [InlineKeyboardButton(text="💵 USD/UAH", callback_data="ticker_UAH=X"), 
         InlineKeyboardButton(text="💶 EUR/USD", callback_data="ticker_EURUSD=X")],
        [InlineKeyboardButton(text="🍎 Apple", callback_data="ticker_AAPL"),
         InlineKeyboardButton(text="🚗 Tesla", callback_data="ticker_TSLA")],
        [InlineKeyboardButton(text="₿ Bitcoin", callback_data="ticker_BTC-USD")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def fetch_price_sync(ticker: str):
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="1d")
        
        if data.empty:
            return None
            
        current_price = data['Close'].iloc[-1]
        currency = stock.info.get('currency', '?')
        
        return f"{current_price:,.2f} {currency}"
    except Exception as e:
        logging.error(f"Error fetching {ticker}: {e}")
        return None

@router.message(CommandStart())
async def start_handler(message: types.Message):
    await message.answer(
        "📈 Hello! I’m a stock market bot.\n\n",
        "Choose an asset from the menu or send me a ticker (for example: NVDA or GOOGL).",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("ticker_"))
async def callback_ticker(callback: CallbackQuery):
    lang = callback.data.split("_")[1]

    await callback.answer(f"Загружаю {ticker}...")
    
    try:
        price = await asyncio.to_thread(fetch_price_sync, ticker)
        
        if price:
            await callback.message.edit_text(
                f"💰 Price **{ticker}**:\n`{price}`",
                parse_mode="Markdown",
                reply_markup=get_main_keyboard()
            )
        else:
            await callback.message.edit_text(
                f"❌ Failed to retrieve data for {ticker}.",
                reply_markup=get_main_keyboard()
            )
    except Exception as e:
        await callback.message.edit_text("❌ Connection error with the exchange.")

@router.message()
async def ticker_handler(message: types.Message):
    ticker = message.text.strip().upper()
    if len(ticker) > 6 or not ticker.isalpha():
        await message.answer("⚠️ Please enter a valid ticker (for example: AAPL).")
        return

    msg = await message.answer(f"🔎 Searching for **{ticker}**...", parse_mode="Markdown")    

    price = await asyncio.to_thread(fetch_price_sync, ticker)
    
    if price:
        await msg.edit_text(
            f"💰 Price of **{ticker}**:\n`{price}`",
            parse_mode="Markdown"
        )
    else:
        await msg.edit_text(f"❌ Ticker **{ticker}** not found.", parse_mode="Markdown")


def get_dispatcher():
    dp = Dispatcher()
    dp.include_router(router)
    return dp