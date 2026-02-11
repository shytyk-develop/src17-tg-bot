import asyncio, logging
import yfinance as yf
from aiogram import Dispatcher, Router, types, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database import add_favorite, get_user_favorites, remove_favorite

router = Router()

# ---------- Keyboards ----------

def main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐️ My Watchlist", callback_data="show_favorites")],
        [InlineKeyboardButton(text="💵 USD/RUB", callback_data="ticker_RUB=X"),
         InlineKeyboardButton(text="💶 EUR/USD", callback_data="ticker_EURUSD=X")],
        [InlineKeyboardButton(text="🍎 Apple", callback_data="ticker_AAPL"),
         InlineKeyboardButton(text="₿ Bitcoin", callback_data="ticker_BTC-USD")],
    ])


def add_fav_keyboard(ticker: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(
        text=f"❤️ Add {ticker}", callback_data=f"fav_add_{ticker}")]])


def del_fav_keyboard(ticker: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(
        text=f"🗑 Remove {ticker}", callback_data=f"fav_del_{ticker}")]])

# ---------- Price Fetch ----------

def fetch_price(ticker: str) -> str | None:
    try:
        stock, data = yf.Ticker(ticker), yf.Ticker(ticker).history(period="1d")
        if data.empty: return None
        price = data["Close"].iloc[-1]
        return f"{price:,.2f} {stock.info.get('currency', '')}"
    except Exception as e:
        logging.error(f"Fetch error {ticker}: {e}"); return None

# ---------- Core Logic ----------

async def show_price(src: types.Message | CallbackQuery, ticker: str) -> None:
    msg = src.message if isinstance(src, CallbackQuery) else src
    await msg.bot.send_chat_action(chat_id=msg.chat.id, action="typing")
    if isinstance(src, CallbackQuery): await src.answer(f"Loading {ticker}...")

    price = await asyncio.to_thread(fetch_price, ticker)
    text = (f"💰 Price **{ticker}**:\n`{price}`" if price
            else f"❌ Failed to retrieve data for {ticker}.")
    kb = add_fav_keyboard(ticker) if price else None

    if isinstance(src, CallbackQuery):
        await msg.edit_text(text, parse_mode="Markdown", reply_markup=kb)
    else:
        await msg.answer(text, parse_mode="Markdown", reply_markup=kb)

# ---------- Handlers ----------

@router.message(CommandStart())
async def start(m: types.Message) -> None:
    await m.answer(
        "📈 **Hello! I am a market bot.**\n\n"
        "I show stock, currency, and crypto prices.\n"
        "Save assets to your watchlist.\n\n"
        "👇 **Choose an action:**",
        reply_markup=main_keyboard(), parse_mode="Markdown")


@router.callback_query(F.data.startswith("ticker_"))
async def cb_ticker(c: CallbackQuery) -> None:
    await show_price(c, c.data.split("_")[1])


@router.message()
async def text_ticker(m: types.Message) -> None:
    t = m.text.strip().upper()
    if len(t) > 8 or not t.replace("-", "").replace("=", "").isalpha(): return
    await show_price(m, t)


@router.callback_query(F.data.startswith("fav_add_"))
async def fav_add(c: CallbackQuery) -> None:
    t, uid = c.data.split("_")[2], c.from_user.id
    ok = await add_favorite(uid, t)
    await c.answer((f"✅ {t} added!" if ok else f"⚠️ {t} already exists."), show_alert=True)


@router.callback_query(F.data == "show_favorites")
async def fav_show(c: CallbackQuery) -> None:
    uid, favs = c.from_user.id, await get_user_favorites(c.from_user.id)
    if not favs:
        await c.answer()
        await c.message.edit_text(
            "📭 Watchlist is empty. Type a ticker and add it.",
            reply_markup=main_keyboard())
        return

    await c.message.edit_text("⏳ Loading prices...")
    prices = await asyncio.gather(*[asyncio.to_thread(fetch_price, t) for t in favs])

    text, kb = "⭐️ **Your watchlist:**\n\n", []
    for t, p in zip(favs, prices):
        text += f"🔹 **{t}**: `{p or 'Error'}`\n"
        kb.append([InlineKeyboardButton(text=f"🗑 Remove {t}", callback_data=f"fav_del_{t}")])
    kb.append([InlineKeyboardButton(text="🔙 Back", callback_data="back_to_main")])

    await c.message.edit_text(text, parse_mode="Markdown",
                              reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))


@router.callback_query(F.data.startswith("fav_del_"))
async def fav_del(c: CallbackQuery) -> None:
    t, uid = c.data.split("_")[2], c.from_user.id
    await remove_favorite(uid, t)
    await c.answer(f"🗑 {t} removed.")
    await fav_show(c)


@router.callback_query(F.data == "back_to_main")
async def back(c: CallbackQuery) -> None:
    await c.message.edit_text("📈 **Main menu**",
                              reply_markup=main_keyboard(),
                              parse_mode="Markdown")

# ---------- Dispatcher ----------

def get_dispatcher() -> Dispatcher:
    dp = Dispatcher(); dp.include_router(router); return dp