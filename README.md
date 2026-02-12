# 📈 Stock & Crypto Price Tracker Bot

![Telegram](https://img.shields.io/badge/Platform-Telegram-0088cc?style=flat-square) ![Python](https://img.shields.io/badge/Python-3.9%2B-3776ab?style=flat-square) ![FastAPI](https://img.shields.io/badge/Framework-FastAPI-009688?style=flat-square) ![SQLAlchemy](https://img.shields.io/badge/ORM-SQLAlchemy-red?style=flat-square) ![License](https://img.shields.io/badge/License-All%20Rights%20Reserved-black?style=flat-square)

**📋 [Overview](#-overview) • [Features](#-features) • [Tech Stack](#-tech-stack) • [Getting Started](#-getting-started) • [API](#-api)**

---

## 🎯 Overview

Asynchronous Telegram bot for tracking prices of stocks, crypto and currencies. Webhook-based architecture, deployed on Vercel. Supports watchlist with personal data storage, generates candlestick charts, works with PostgreSQL/SQLite.

**Stack**: FastAPI + Aiogram + SQLAlchemy Async + yfinance + mplfinance

---

## ✨ Features

- **Real-time prices** → yfinance API (AAPL, BTC-USD, EURUSD=X)
- **Personal Watchlist** → PostgreSQL with user_id isolation
- **Charts** → 1 month candlestick charts in PNG
- **Webhook** → instead of polling, optimal for Vercel
- **Full type hints** + async/await everywhere
- **SQL Injection safe** → SQLAlchemy ORM

---

## 📚 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Bot** | Aiogram 3.x |
| **API** | FastAPI + Uvicorn |
| **DB** | SQLAlchemy async + asyncpg (PostgreSQL) / aiosqlite (SQLite) |
| **Data** | yfinance + pandas + mplfinance |
| **Deploy** | Vercel Serverless |

---

## 🏗️ Architecture

```
User Input (Telegram)
    ↓
Webhook: POST / (FastAPI)
    ↓
Update.model_validate() → Dispatcher.feed_update()
    ↓
Router handlers (@router.message / @router.callback_query)
    ↓
├─ fetch_price(ticker) → yfinance
├─ generate_chart(ticker) → mplfinance
└─ Database CRUD (add/remove/get favorites)
    ↓
SQLAlchemy async → PostgreSQL
    ↓
Bot.edit_text() / answer_photo()
    ↓
Telegram Response
```

**3 Core Components:**

1. **bot_instance.py** (380 lines)
   - Handlers/keyboards/business logic
   - Filters: `CommandStart()`, `Command()`, `F.data.startswith()`
   - `asyncio.to_thread()` for yfinance/mplfinance, `asyncio.gather()` for parallel loading

2. **database.py** (70 lines)
   - Favorite ORM model (user_id + ticker)
   - CRUD: `add_favorite()` (duplicate check), `remove_favorite()`, `get_user_favorites()`
   - Auto-parse `postgres://` → `postgresql+asyncpg://`

3. **api/index.py** (50 lines)
   - FastAPI + lifespan context manager
   - Webhook handler: `POST /` → aiogram dispatcher
   - Lazy DB initialization

---

## ⚙️ Getting Started

### Localhost + SQLite

```bash
git clone https://github.com/shytyk-develop/telegram-bot.git
cd telegram-bot
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

cat > .env << EOF
BOT_TOKEN=your_token
DATABASE_URL=sqlite+aiosqlite:///:memory:
EOF
```

### Vercel + PostgreSQL

```bash
# Deploy
vercel --prod

# Env vars (Vercel dashboard)
BOT_TOKEN = ...
DATABASE_URL = postgresql+asyncpg://user:pass@host/db

# Webhook
curl -X POST https://api.telegram.org/botTOKEN/setWebhook \
  -d url=https://your-app.vercel.app/
```

---

## 🔄 API

### Handlers

```python
@router.message(CommandStart())              # /start
@router.message(Command("help"))             # /help
@router.message()                            # Text (ticker)
@router.callback_query(F.data == "...")      # Exact match
@router.callback_query(F.data.startswith("fav_"))  # Prefix parsing
```

### Core Operations

```python
# Price
price, currency = await asyncio.to_thread(fetch_price, "AAPL")
# → ("150.25", "USD")

# Chart
buf = await asyncio.to_thread(generate_chart, "BTC-USD")
# → BytesIO → await message.answer_photo()

# Watchlist
await add_favorite(user_id=123, ticker="AAPL")
favorites = await get_user_favorites(user_id=123)
await remove_favorite(user_id=123, ticker="AAPL")

# Messages
await message.answer(text, parse_mode="Markdown", reply_markup=kb)
await message.edit_text(new_text, parse_mode="Markdown")
await message.answer_photo(photo=BufferedInputFile(buf.read()))
```

### yfinance

```python
stock = yf.Ticker("AAPL")
data = stock.history(period="1d")
price = data["Close"].iloc[-1]
currency = stock.info.get("currency", "USD")
df = stock.history(period="1mo")  # for chart
```

### mplfinance

```python
mc = mpf.make_marketcolors(up='green', down='red')
s = mpf.make_mpf_style(marketcolors=mc)
mpf.plot(df, type='candle', style=s, 
         savefig=dict(fname=buffer, dpi=100))
```

---

## 🗄️ Database

```sql
CREATE TABLE favorites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id BIGINT NOT NULL,
    ticker VARCHAR NOT NULL,
    UNIQUE(user_id, ticker),
    INDEX idx_user_id (user_id)
);
```

**SQLAlchemy Model:**
```python
class Favorite(Base):
    __tablename__ = "favorites"
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, index=True)
    ticker = Column(String)
```

---

## 🔐 Security

- **SQLAlchemy ORM** → parameterized queries (SQL injection protection)
- **Webhook validation** → built-in to aiogram
- **SSL/TLS** → ssl_context for PostgreSQL
- **User isolation** → data stored with user_id, filtered by it

---

## 📊 Performance

| Operation | Time |
|-----------|------|
| Price (yfinance) | 200-500ms |
| Watchlist (4 assets) | 800ms-2s |
| Chart | 1-3s |
| DB query | 10-50ms |

**Optimization**: Webhook (not polling), `asyncio.gather()`, connection pooling, asyncpg

---

## 📁 Structure

```
├── bot_instance.py       # Handlers, keyboards, price/chart
├── database.py           # ORM, CRUD, connection
├── api/index.py          # FastAPI webhook app
├── requirements.txt
├── vercel.json           # Rewrites config
└── README.md
```

---

## ⚖️ License

**© 2026 Yan Shytyk. All Rights Reserved.**

This project is the sole property of the author. The source code is provided for educational purposes and to demonstrate programming skills.

### ✅ Permitted:
- Viewing the source code for educational purposes
- Code analysis and studying approaches
- Using to understand architecture and patterns

### ❌ Prohibited:
- Commercial use without author's permission
- Copying and using in your own projects
- Distribution or publication of modified versions
- Using as a basis for other products

For permission inquiries, contact the author.

---

Made with ❤️ by [@shytyk-develop](https://github.com/shytyk-develop) | If you find it useful, give it a ⭐️!

