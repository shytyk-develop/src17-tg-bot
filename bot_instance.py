import asyncio, logging
import yfinance as yf
from aiogram import Dispatcher, Router, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database import add_favorite, get_user_favorites, remove_favorite

router = Router()

# ---------- Keyboards ----------

def main_keyboard() -> InlineKeyboardMarkup:
    """Main menu with logical navigation"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐️ Watchlist", callback_data="menu_watchlist"),
        InlineKeyboardButton(text="🔍 Search Asset", callback_data="menu_search")],
    ])


def watchlist_keyboard(has_items: bool) -> InlineKeyboardMarkup:
    """Watchlist menu with Edit and Back buttons"""
    buttons = []
    if has_items:
        buttons.append([InlineKeyboardButton(text="✏️ Edit", callback_data="watchlist_edit")])
    buttons.append([InlineKeyboardButton(text="🔙 Back", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def edit_watchlist_keyboard(tickers: list) -> InlineKeyboardMarkup:
    """Edit watchlist - individual delete buttons and back"""
    buttons = [[InlineKeyboardButton(text=f"🗑 Remove {t}", callback_data=f"fav_del_{t}")] for t in tickers]
    buttons.append([InlineKeyboardButton(text="🔙 Back", callback_data="back_to_watchlist")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def price_keyboard(ticker: str, is_favorite: bool = False) -> InlineKeyboardMarkup:
    """Price display keyboard - Add to watchlist or Remove from watchlist, and Back"""
    buttons = []
    if is_favorite:
        buttons.append([InlineKeyboardButton(text=f"🗑 Remove from Watchlist", callback_data=f"fav_del_{ticker}")])
    else:
        buttons.append([InlineKeyboardButton(text=f"❤️ Add to Watchlist", callback_data=f"fav_add_{ticker}")])
    buttons.append([InlineKeyboardButton(text="🔙 Back to Search", callback_data="menu_search")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def search_menu_keyboard() -> InlineKeyboardMarkup:
    """Search menu with quick examples and back"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Back to Menu", callback_data="back_to_main")],
    ])

# ---------- Price Fetch ----------

def fetch_price(ticker: str) -> tuple[str, str] | tuple[None, None]:
    """Fetch price and currency for a ticker."""
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="1d")
        if data.empty:
            return None, None
        price = data["Close"].iloc[-1]
        currency = stock.info.get('currency', 'USD')
        price_str = f"{price:,.2f}"
        return price_str, currency
    except Exception as e:
        logging.error(f"Fetch error {ticker}: {e}")
        return None, None

# ---------- Core Logic ----------

async def show_price(m: types.Message, ticker: str, edit: bool = False, callback: CallbackQuery = None) -> None:
    """Display price for ticker."""
    if callback:
        await callback.message.edit_text("⏳ Loading price...")
    elif edit:
        await m.edit_text("⏳ Loading price...")
    
    price, currency = await asyncio.to_thread(fetch_price, ticker)
    
    if price:
        text = f"💰 **Price for {ticker}**\n\n`{price} {currency}`"
        favorites = await get_user_favorites(callback.from_user.id if callback else m.from_user.id)
        is_favorite = ticker in favorites
    else:
        text = f"❌ Could not retrieve data for **{ticker}**.\n\nTry a different ticker."
        is_favorite = False
    
    kb = price_keyboard(ticker, is_favorite)
    user_id = callback.from_user.id if callback else m.from_user.id
    chat_id = callback.message.chat.id if callback else m.chat.id
    
    if callback:
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
        await callback.answer()
    elif edit:
        await m.edit_text(text, parse_mode="Markdown", reply_markup=kb)
    else:
        await m.answer(text, parse_mode="Markdown", reply_markup=kb)

# ---------- Handlers ----------

@router.message(CommandStart())
async def start(m: types.Message) -> None:
    """Start command - show main menu"""
    await m.answer(
        "📈 **Stock & Crypto Price Tracker**\n\n"
        "Track your favorite assets and get real-time prices.\n\n"
        "👇 **Choose an option:**",
        reply_markup=main_keyboard(), 
        parse_mode="Markdown"
    )


@router.message(Command("help"))
async def help_command(m: types.Message) -> None:
    """Help command - show help menu"""
    text = (
        "ℹ️ **How to use this bot**\n\n"
        "**⭐️ Watchlist**\n"
        "View your favorite assets with real-time prices.\n"
        "• Tap **Edit** to remove items\n"
        "• Tap **Back** to return to menu\n\n"
        "**🔍 Search Asset**\n"
        "Find any stock, crypto, or currency price.\n"
        "Just type the ticker symbol.\n\n"
        "**Supported Assets:**\n"
        "• US Stocks: `AAPL`, `GOOGL`, `MSFT`, etc.\n"
        "• Cryptocurrencies: `BTC-USD`, `ETH-USD`, etc.\n"
        "• Currencies: `EURUSD=X`, `GBPUSD=X`, etc.\n\n"
        "**Need help?**\n"
        "Use /start to return to main menu."
    )
    
    await m.answer(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="GitHub", url="https://github.com/shytyk-develop")],
            [InlineKeyboardButton(text="🔙 Back", callback_data="back_to_main")]
        ]),
        parse_mode="Markdown"
    )


# ========== MAIN MENU ==========

@router.callback_query(F.data == "back_to_main")
async def back_to_main(c: CallbackQuery) -> None:
    """Return to main menu"""
    await c.message.edit_text(
        "📈 **Stock & Crypto Price Tracker**\n\n"
        "Track your favorite assets and get real-time prices.\n\n"
        "👇 **Choose an option:**",
        reply_markup=main_keyboard(),
        parse_mode="Markdown"
    )
    await c.answer()


# ========== WATCHLIST ==========

@router.callback_query(F.data == "menu_watchlist")
async def show_watchlist(c: CallbackQuery) -> None:
    """Show user's watchlist with prices"""
    favs = await get_user_favorites(c.from_user.id)
    
    if not favs:
        await c.message.edit_text(
            "📭 **Your watchlist is empty**\n\n"
            "Use **Search Asset** to find and add stocks, currencies, or crypto.",
            reply_markup=watchlist_keyboard(False),
            parse_mode="Markdown"
        )
        await c.answer()
        return
    
    await c.message.edit_text("⏳ Loading prices...", parse_mode="Markdown")
    prices = await asyncio.gather(*[asyncio.to_thread(fetch_price, t) for t in favs])
    
    text = "⭐️ **Your Watchlist**\n\n"
    for ticker, (price, currency) in zip(favs, prices):
        if price:
            text += f"🔹 **{ticker}** → `{price} {currency}`\n"
        else:
            text += f"🔹 **{ticker}** → ❌ Error\n"
    
    await c.message.edit_text(
        text,
        reply_markup=watchlist_keyboard(True),
        parse_mode="Markdown"
    )
    await c.answer()


@router.callback_query(F.data == "watchlist_edit")
async def edit_watchlist(c: CallbackQuery) -> None:
    """Edit watchlist - show remove buttons"""
    favs = await get_user_favorites(c.from_user.id)
    
    if not favs:
        await c.answer("Your watchlist is empty!", show_alert=True)
        return
    
    text = "✏️ **Edit Watchlist**\n\n"
    text += "Tap a ticker to remove it:\n\n"
    for t in favs:
        text += f"🔹 {t}\n"
    
    await c.message.edit_text(
        text,
        reply_markup=edit_watchlist_keyboard(favs),
        parse_mode="Markdown"
    )
    await c.answer()


@router.callback_query(F.data == "back_to_watchlist")
async def back_to_watchlist(c: CallbackQuery) -> None:
    """Return to watchlist from edit"""
    await show_watchlist(c)


@router.callback_query(F.data.startswith("fav_add_"))
async def fav_add(c: CallbackQuery) -> None:
    """Add ticker to favorites"""
    ticker = c.data.split("_")[2]
    user_id = c.from_user.id
    ok = await add_favorite(user_id, ticker)
    if ok:
        await c.answer(f"✅ {ticker} added to watchlist!", show_alert=True)
    else:
        await c.answer(f"⚠️ {ticker} is already in your watchlist.", show_alert=True)


@router.callback_query(F.data.startswith("fav_del_"))
async def fav_del(c: CallbackQuery) -> None:
    """Remove ticker from favorites"""
    ticker = c.data.split("_")[2]
    user_id = c.from_user.id
    await remove_favorite(user_id, ticker)
    await c.answer(f"🗑 {ticker} removed from watchlist.", show_alert=True)
    
    if "watchlist_edit" in c.message.text or "Edit Watchlist" in c.message.text:
        await edit_watchlist(c)
    else:
        await show_watchlist(c)


# ========== SEARCH ==========

@router.callback_query(F.data == "menu_search")
async def search_menu(c: CallbackQuery) -> None:
    """Show search menu with instructions"""
    text = (
        "🔍 **Search for Assets**\n\n"
        "📝 **How to use:**\n"
        "Simply type a ticker symbol to get the current price.\n\n"
        "**Examples:**\n"
        "• Stocks: `AAPL`, `GOOGL`, `MSFT`\n"
        "• Crypto: `BTC-USD`, `ETH-USD`\n"
        "• Currency: `EURUSD=X`, `GBPUSD=X`\n\n"
        "⬇️ **Type a ticker below to search:**"
    )
    
    await c.message.edit_text(
        text,
        reply_markup=search_menu_keyboard(),
        parse_mode="Markdown"
    )
    await c.answer()


@router.message()
async def search_ticker(m: types.Message) -> None:
    """Handle ticker input from user"""
    ticker = m.text.strip().upper()
    
    if len(ticker) > 15 or not all(c.isalnum() or c in "-=" for c in ticker):
        await m.answer(
            "❌ **Invalid ticker format**\n\n"
            "Use only letters, numbers, hyphens, and equal signs.\n"
            "Examples: `AAPL`, `BTC-USD`, `EURUSD=X`",
            parse_mode="Markdown"
        )
        return
    
    await show_price(m, ticker)


# ========== HELP ==========

@router.callback_query(F.data == "menu_help")
async def help_menu(c: CallbackQuery) -> None:
    """Show help menu"""
    text = (
        "ℹ️ **How to use this bot**\n\n"
        "**⭐️ My Watchlist**\n"
        "View your favorite assets with real-time prices.\n"
        "• Tap **Edit** to remove items\n"
        "• Tap **Back** to return to menu\n\n"
        "**🔍 Search Asset**\n"
        "Find any stock, crypto, or currency price.\n"
        "Just type the ticker symbol.\n\n"
        "**Supported Assets:**\n"
        "• US Stocks: `AAPL`, `GOOGL`, `MSFT`, etc.\n"
        "• Cryptocurrencies: `BTC-USD`, `ETH-USD`, etc.\n"
        "• Currencies: `EURUSD=X`, `GBPUSD=X`, etc.\n\n"
        "**Need help?**\n"
        "Use /start to return to main menu."
    )
    
    await c.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="GitHub", url="https://github.com/shytyk-develop")],
            [InlineKeyboardButton(text="🔙 Back", callback_data="back_to_main")]
        ]),
        parse_mode="Markdown"
    )
    await c.answer()

# ---------- Dispatcher ----------

def get_dispatcher() -> Dispatcher:
    dp = Dispatcher(); dp.include_router(router); return dp