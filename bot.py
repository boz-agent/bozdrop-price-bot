#!/usr/bin/env python3
"""
🟠 Bozdrop Price Bot v3 — Dynamic Lookup
Supports ALL 19,000+ tokens from CryptoCompare!
"""

import os
import sys
import re
import time
import json
import logging
import requests
from typing import Optional, Dict, List, Tuple
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# --- Config ---
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CACHE_DIR = os.environ.get("CACHE_DIR", "/tmp/bozdrop-bot-cache")
COINS_CACHE_FILE = os.path.join(CACHE_DIR, "coins_cache.json")
CACHE_TTL = 86400  # 24 hours

# --- Logging ---
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    stream=sys.stdout,
    force=True
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# --- Global State ---
coins_by_symbol = {}  # type: Dict[str, Dict]
last_coins_fetch = 0

# Fiat display symbols
FIAT_DISPLAY = {
    "idr": "Rp", "usd": "$", "eur": "€", "gbp": "£", "jpy": "¥",
    "sgd": "S$", "aud": "A$", "cad": "C$", "cny": "¥", "inr": "₹",
    "krw": "₩", "thb": "฿", "php": "₱", "myr": "RM", "vnd": "₫",
    "rub": "₽", "try": "₺", "brl": "R$", "mxn": "MXN", "zar": "R",
    "aed": "AED", "hkd": "HK$", "twd": "NT$", "usdt": "$",
    "chf": "CHF", "sek": "SEK", "nok": "NOK", "dkk": "DKK",
    "pln": "PLN", "czk": "CZK", "huf": "HUF", "ils": "₪",
}

FIAT_SYMBOLS = set(FIAT_DISPLAY.keys())

# Price cache
price_cache = {}  # type: Dict[str, Tuple[float, float]]
PRICE_CACHE_TTL = 60


def load_coins_from_cache():
    """Load coins from local cache."""
    global coins_by_symbol, last_coins_fetch
    
    try:
        if os.path.exists(COINS_CACHE_FILE):
            with open(COINS_CACHE_FILE, 'r') as f:
                data = json.load(f)
                coins_by_symbol = data.get('by_symbol', {})
                last_coins_fetch = data.get('timestamp', 0)
                
                if time.time() - last_coins_fetch < CACHE_TTL:
                    logger.info(f"Loaded {len(coins_by_symbol)} coins from cache")
                    return True
    except Exception as e:
        logger.error(f"Cache load error: {e}")
    
    return False


def save_coins_to_cache():
    """Save coins to local cache."""
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        data = {
            'by_symbol': coins_by_symbol,
            'timestamp': last_coins_fetch
        }
        with open(COINS_CACHE_FILE, 'w') as f:
            json.dump(data, f)
        logger.info(f"Cached {len(coins_by_symbol)} coins")
    except Exception as e:
        logger.error(f"Cache save error: {e}")


def fetch_coins_list():
    """Fetch coins list from CryptoCompare."""
    global coins_by_symbol, last_coins_fetch
    
    logger.info("Fetching coins list from CryptoCompare...")
    
    try:
        url = "https://min-api.cryptocompare.com/data/all/coinlist"
        resp = requests.get(url, timeout=30)
        
        if resp.status_code == 200:
            data = resp.json().get('Data', {})
            
            coins_by_symbol = {}
            
            for coin_key, coin_info in data.items():
                symbol = coin_info.get('Symbol', '').upper()
                name = coin_info.get('CoinName', '')
                
                if not symbol:
                    continue
                
                if symbol not in coins_by_symbol:
                    coins_by_symbol[symbol] = {
                        'name': name,
                        'key': coin_key
                    }
            
            last_coins_fetch = time.time()
            save_coins_to_cache()
            
            logger.info(f"Loaded {len(coins_by_symbol)} coins")
            return True
        else:
            logger.error(f"CryptoCompare returned {resp.status_code}")
            
    except Exception as e:
        logger.error(f"Error fetching coins: {e}")
    
    return False


def find_symbol(symbol):
    """Find and normalize symbol. Returns uppercase or None."""
    symbol = symbol.upper()
    
    # Common aliases
    ALIASES = {
        "BITCOIN": "BTC",
        "ETHEREUM": "ETH",
        "SOLANA": "SOL",
        "BINANCE": "BNB",
        "BINANCECOIN": "BNB",
        "RIPPLE": "XRP",
        "DOGECOIN": "DOGE",
        "CARDANO": "ADA",
        "POLKADOT": "DOT",
        "AVALANCHE": "AVAX",
        "CHAINLINK": "LINK",
        "POLYGON": "MATIC",
        "TRON": "TRX",
        "COSMOS": "ATOM",
        "UNISWAP": "UNI",
        "LITECOIN": "LTC",
        "ETHEREUMCLASSIC": "ETC",
        "STELLAR": "XLM",
        "NEAR": "NEAR",
        "ALGORAND": "ALGO",
        "FANTOM": "FTM",
        "TEZOS": "XTZ",
        "EOS": "EOS",
        "AAVE": "AAVE",
        "MAKER": "MKR",
        "COMPOUND": "COMP",
        "SYNTHETIX": "SNX",
        "THEGRAPH": "GRT",
        "FILECOIN": "FIL",
        "INTERNETCOMPUTER": "ICP",
        "VECHAIN": "VET",
        "SHIBA": "SHIB",
        "SHIBAINU": "SHIB",
        "PEPE": "PEPE",
        "FLOKI": "FLOKI",
        "BONK": "BONK",
        "WIF": "WIF",
        "JUPITER": "JUP",
        "JITO": "JTO",
        "PYTH": "PYTH",
        "WORMHOLE": "W",
        "STARKNET": "STRK",
        "SEI": "SEI",
        "CELESTIA": "TIA",
        "APTOS": "APT",
        "SUI": "SUI",
        "ARBITRUM": "ARB",
        "OPTIMISM": "OP",
        "BLUR": "BLUR",
        "OPENSEA": "OS",
        "TETHER": "USDT",
        "USDTCOIN": "USDT",
        "BINANCEUSD": "BUSD",
        "USDCCOIN": "USDC",
        "DAI": "DAI",
    }
    
    if symbol in ALIASES:
        return ALIASES[symbol]
    
    if symbol in coins_by_symbol:
        return symbol
    
    return None


def fetch_price(symbol, vs_currency):
    """Fetch price from CryptoCompare."""
    symbol = symbol.upper()
    vs_currency = vs_currency.lower()
    
    if vs_currency in ['usdt', 'usd']:
        vs_currency = 'USD'
    
    cache_key = f"price:{symbol}:{vs_currency}"
    
    if cache_key in price_cache:
        price, ts = price_cache[cache_key]
        if time.time() - ts < PRICE_CACHE_TTL:
            return price
    
    try:
        url = f"https://min-api.cryptocompare.com/data/price?fsym={symbol}&tsyms={vs_currency.upper()}"
        resp = requests.get(url, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            
            if 'Error' in data:
                return None
            
            if vs_currency.upper() in data:
                price = float(data[vs_currency.upper()])
                price_cache[cache_key] = (price, time.time())
                return price
                
    except Exception as e:
        logger.error(f"Error fetching price: {e}")
    
    return None


def format_number(num, currency):
    """Format number based on currency."""
    currency = currency.lower()
    
    if currency == "idr":
        return f"{int(num):,}".replace(",", ".")
    elif currency in ["jpy", "krw", "vnd"]:
        return f"{int(num):,}"
    elif num < 0.0000001:
        return f"{num:.12f}"
    elif num < 0.00001:
        return f"{num:.10f}"
    elif num < 0.001:
        return f"{num:.8f}"
    elif num < 0.1:
        return f"{num:.6f}"
    elif num < 1:
        return f"{num:.4f}"
    else:
        return f"{num:,.2f}"


def parse_message(text):
    """Parse '1 btc idr' or '0.5 eth usd'."""
    text = text.strip().lower()
    text = re.sub(r'\s+to\s+', ' ', text)
    
    pattern = r"^(\d+(?:\.\d+)?)\s*([a-z0-9\-\.]+)\s+([a-z]{3,4})$"
    match = re.match(pattern, text)
    
    if match:
        amount = float(match.group(1))
        crypto = match.group(2).upper()
        fiat = match.group(3).lower()
        
        if fiat in FIAT_SYMBOLS:
            return (amount, crypto, fiat)
    
    return None


async def handle_message(update, context):
    """Handle incoming message."""
    if not update.message or not update.message.text:
        return
    
    text = update.message.text.strip()
    
    if text.startswith("/") or text.startswith("!"):
        return
    
    parsed = parse_message(text)
    if not parsed:
        return
    
    amount, crypto, fiat = parsed
    
    symbol = find_symbol(crypto)
    if not symbol:
        await update.message.reply_text(
            f"❌ Token `{crypto}` tidak ditemukan.\n"
            f"Ketik `/help` untuk info.",
            parse_mode="Markdown"
        )
        return
    
    coin_info = coins_by_symbol.get(symbol, {})
    coin_name = coin_info.get('name', symbol)
    
    price = fetch_price(symbol, fiat)
    if price is None:
        await update.message.reply_text("⚠️ Gagal ambil harga. Coba lagi sebentar.")
        return
    
    total = amount * price
    
    fiat_display = FIAT_DISPLAY.get(fiat, fiat.upper())
    formatted_price = format_number(price, fiat)
    formatted_total = format_number(total, fiat)
    
    reply = (
        f"**💰 {amount} {symbol} = {fiat_display} {formatted_total}**\n\n"
        f"📊 1 {symbol} = {fiat_display} {formatted_price}\n"
        f"📝 {coin_name}\n"
        f"🕐 Live CryptoCompare"
    )
    
    await update.message.reply_text(reply, parse_mode="Markdown")


async def handle_start(update, context):
    """Handle /start command."""
    total = len(coins_by_symbol)
    welcome = (
        f"🟠 **Bozdrop Price Bot**\n\n"
        f"Support **{total:,}+ token** dari CryptoCompare!\n\n"
        f"**Cara pakai:**\n"
        f"`1 btc idr`\n"
        f"`0.5 eth usd`\n"
        f"`1000000 pepe idr`\n\n"
        f"Format: `[jumlah] [crypto] [fiat]`"
    )
    await update.message.reply_text(welcome, parse_mode="Markdown")


async def handle_help(update, context):
    """Handle /help command."""
    total = len(coins_by_symbol)
    help_text = (
        f"🟠 **Bantuan**\n\n"
        f"Support **{total:,}+ token**!\n\n"
        f"**Contoh:**\n"
        f"`1 btc idr` → Bitcoin ke Rupiah\n"
        f"`0.5 eth usd` → Ethereum ke Dollar\n"
        f"`10 sol idr` → Solana ke Rupiah\n\n"
        f"**Fiat:** IDR, USD, EUR, SGD, AUD, dll\n\n"
        f"**Commands:**\n"
        f"/start - Info bot\n"
        f"/help - Bantuan\n"
        f"/coins - Info jumlah token"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def handle_coins(update, context):
    """Handle /coins command."""
    total = len(coins_by_symbol)
    cache_age = int((time.time() - last_coins_fetch) / 60)
    
    coins_text = (
        f"🟠 **Token Supported**\n\n"
        f"📊 Total: **{total:,}** token\n"
        f"🕐 Cache: {cache_age} menit lalu\n\n"
        f"Ketik symbol apa aja — bot detect otomatis!"
    )
    await update.message.reply_text(coins_text, parse_mode="Markdown")


def main():
    """Run the bot."""
    if not BOT_TOKEN:
        print("ERROR: Set TELEGRAM_BOT_TOKEN environment variable!")
        sys.exit(1)
    
    print("Bozdrop Price Bot v3 starting...")
    
    # Load coins list
    if not load_coins_from_cache():
        fetch_coins_list()
    
    print(f"Loaded {len(coins_by_symbol)} coins")
    print("Bot running!")
    
    # Create app
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.Regex(r"^/start$"), handle_start))
    app.add_handler(MessageHandler(filters.Regex(r"^/help$"), handle_help))
    app.add_handler(MessageHandler(filters.Regex(r"^/coins$"), handle_coins))
    
    # Run
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
