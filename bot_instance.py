import asyncio
import logging
import yfinance as yf
from aiogram import Bot, Dispatcher, Router, types, F
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

def fetch_price_sync(ticker_symbol: str):
    try:
        stock = yf.Ticker(ticker_symbol)
        data = stock.history(period="1d")
        
        if data.empty:
            return None
            
        current_price = data['Close'].iloc[-1]
        currency = stock.info.get('currency', '?')
        
        return f"{current_price:,.2f} {currency}"
    except Exception as e:
        logging.error(f"Error fetching {ticker_symbol}: {e}")
        return None

@router.message(CommandStart())
async def start_handler(message: types.Message):
    text = (
        "📈 **Hello! I’m a stock market bot.**\n\n"
        "Choose an asset from the menu or send me a ticker (for example: `NVDA` or `GOOGL`)."
    )
    await message.answer(
        text,
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("ticker_"))
async def callback_ticker(callback: CallbackQuery):
    ticker_symbol = callback.data.split("_")[1]

    await callback.answer(f"Loading {ticker_symbol}...")
    
    try:
        price = await asyncio.to_thread(fetch_price_sync, ticker_symbol)
        
        if price:
            await callback.message.edit_text(
                f"💰 Price **{ticker_symbol}**:\n`{price}`",
                parse_mode="Markdown",
                reply_markup=get_main_keyboard()
            )
        else:
            await callback.message.edit_text(
                f"❌ Failed to retrieve data for {ticker_symbol}.",
                reply_markup=get_main_keyboard()
            )
    except Exception as e:
        print(f"Callback error: {e}")
        await callback.message.edit_text("❌ Connection error with the exchange.", reply_markup=get_main_keyboard())

@router.message()
async def ticker_handler(message: types.Message):
    ticker_symbol = message.text.strip().upper()
    
    if len(ticker_symbol) > 6 or not ticker_symbol.replace("-", "").replace("=", "").isalpha():
        await message.answer("⚠️ Please enter a valid ticker (for example: AAPL).")
        return

    msg = await message.answer(f"🔎 Searching for **{ticker_symbol}**...", parse_mode="Markdown")    

    price = await asyncio.to_thread(fetch_price_sync, ticker_symbol)
    
    if price:
        await msg.edit_text(
            f"💰 Price of **{ticker_symbol}**:\n`{price}`",
            parse_mode="Markdown"
        )
    else:
        await msg.edit_text(f"❌ Ticker **{ticker_symbol}** not found.", parse_mode="Markdown")

def get_dispatcher():
    dp = Dispatcher()
    dp.include_router(router)
    return dp