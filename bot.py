#!/usr/bin/env python3
"""
🟠 Bozdrop Price Bot v3 — Dynamic Lookup
Supports ALL 19,000+ tokens from CryptoCompare!

Usage:
  User: 1 btc idr
  Bot:  💰 1 BTC = Rp 1,542,360,000
"""

import os
import sys
import re
import time
import json
import logging
import requests
from typing import Optional, Dict, List
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# --- Config ---
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CACHE_DIR = os.path.expanduser("~/.hermes/hermes-agent/bozdrop-price-bot")
COINS_CACHE_FILE = os.path.join(CACHE_DIR, "coins_cache.json")
CACHE_TTL = 86400  # 24 hours for coins list

# --- Logging ---
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    stream=sys.stdout
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# --- Global State ---
coins_by_symbol: Dict[str, Dict] = {}  # {"BTC": {"name": "Bitcoin", ...}, ...}
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

# Fiat symbols accepted
FIAT_SYMBOLS = set(FIAT_DISPLAY.keys()) | {
    "idr", "usd", "eur", "gbp", "jpy", "sgd", "aud", "cad", 
    "cny", "inr", "krw", "thb", "php", "myr", "vnd", "rub", 
    "try", "brl", "mxn", "zar", "aed", "hkd", "twd", "usdt",
    "chf", "sek", "nok", "dkk", "pln", "czk", "huf", "ils",
}

# Price cache
price_cache: Dict[str, tuple] = {}
PRICE_CACHE_TTL = 60  # 60 seconds

# USD to IDR cache (for conversion)
usd_idr_rate = 16500  # Default rate


def load_coins_from_cache() -> bool:
    """Load coins from local cache."""
    global coins_by_symbol, last_coins_fetch
    
    try:
        if os.path.exists(COINS_CACHE_FILE):
            with open(COINS_CACHE_FILE, 'r') as f:
                data = json.load(f)
                coins_by_symbol = data.get('by_symbol', {})
                last_coins_fetch = data.get('timestamp', 0)
                
                if time.time() - last_coins_fetch < CACHE_TTL:
                    logger.info(f"✅ Loaded {len(coins_by_symbol)} coins from cache")
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
        logger.info(f"✅ Cached {len(coins_by_symbol)} coins")
    except Exception as e:
        logger.error(f"Cache save error: {e}")


def fetch_coins_list() -> bool:
    """Fetch coins list from CryptoCompare."""
    global coins_by_symbol, last_coins_fetch
    
    logger.info("📡 Fetching coins list from CryptoCompare...")
    
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
                
                # Some coins have same symbol (e.g., different tokens)
                # We'll store them with highest priority (usually the main one)
                if symbol not in coins_by_symbol:
                    coins_by_symbol[symbol] = {
                        'name': name,
                        'key': coin_key
                    }
            
            last_coins_fetch = time.time()
            save_coins_to_cache()
            
            logger.info(f"✅ Loaded {len(coins_by_symbol)} coins")
            return True
        else:
            logger.error(f"CryptoCompare returned {resp.status_code}")
            
    except Exception as e:
        logger.error(f"Error fetching coins: {e}")
    
    return False


def find_symbol(symbol: str) -> Optional[str]:
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
    
    # Check if symbol exists in database
    if symbol in coins_by_symbol:
        return symbol
    
    # Try partial match
    for coin_symbol in coins_by_symbol:
        if coin_symbol.startswith(symbol) or symbol.startswith(coin_symbol):
            return coin_symbol
    
    return None


def update_usd_idr_rate():
    """Update USD to IDR rate."""
    global usd_idr_rate
    
    try:
        url = "https://min-api.cryptocompare.com/data/price?fsym=USD&tsyms=IDR"
        resp = requests.get(url, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            if 'IDR' in data:
                usd_idr_rate = data['IDR']
                logger.info(f"📊 USD/IDR rate: {usd_idr_rate:,.0f}")
    except:
        pass


def fetch_price(symbol: str, vs_currency: str) -> Optional[float]:
    """Fetch price from CryptoCompare."""
    symbol = symbol.upper()
    vs_currency = vs_currency.lower()
    
    # Handle USDT as USD
    if vs_currency in ['usdt', 'usd']:
        vs_currency = 'USD'
    
    cache_key = f"price:{symbol}:{vs_currency}"
    
    # Check cache
    if cache_key in price_cache:
        price, ts = price_cache[cache_key]
        if time.time() - ts < PRICE_CACHE_TTL:
            return price
    
    # Fetch from API
    try:
        url = f"https://min-api.cryptocompare.com/data/price?fsym={symbol}&tsyms={vs_currency.upper()}"
        resp = requests.get(url, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            
            if 'Error' in data:
                logger.error(f"CryptoCompare error: {data.get('Message', 'Unknown')}")
                return None
            
            if vs_currency.upper() in data:
                price = float(data[vs_currency.upper()])
                price_cache[cache_key] = (price, time.time())
                return price
            
    except Exception as e:
        logger.error(f"Error fetching price: {e}")
    
    return None


def fetch_multi_price(symbols: List[str], vs_currency: str) -> Dict[str, float]:
    """Fetch multiple prices at once (more efficient)."""
    vs_currency = vs_currency.upper()
    if vs_currency in ['USDT']:
        vs_currency = 'USD'
    
    syms = ','.join([s.upper() for s in symbols])
    
    try:
        url = f"https://min-api.cryptocompare.com/data/pricemulti?fsyms={syms}&tsyms={vs_currency}"
        resp = requests.get(url, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            
            if 'Error' not in data:
                result = {}
                for sym, prices in data.items():
                    if vs_currency in prices:
                        result[sym] = prices[vs_currency]
                return result
    except Exception as e:
        logger.error(f"Error fetching multi price: {e}")
    
    return {}


def format_number(num: float, currency: str) -> str:
    """Format number based on currency."""
    currency = currency.lower()
    
    if currency == "idr":
        # IDR: no decimals, dots for thousands
        return f"{int(num):,}".replace(",", ".")
    elif currency in ["jpy", "krw", "vnd"]:
        # No decimals
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


def parse_message(text: str) -> Optional[tuple]:
    """Parse '1 btc idr' or '0.5 eth usd'."""
    text = text.strip().lower()
    
    # Handle "1 btc to idr" format
    text = re.sub(r'\s+to\s+', ' ', text)
    
    # Match: amount + crypto + fiat
    patterns = [
        r"^(\d+(?:\.\d+)?)\s*([a-z0-9\-\.]+)\s+([a-z]{3,4})$",
    ]
    
    for pattern in patterns:
        match = re.match(pattern, text)
        if match:
            amount = float(match.group(1))
            crypto = match.group(2).upper()
            fiat = match.group(3).lower()
            
            if fiat in FIAT_SYMBOLS:
                return (amount, crypto, fiat)
    
    return None


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming message."""
    if not update.message or not update.message.text:
        return
    
    text = update.message.text.strip()
    
    # Skip commands
    if text.startswith("/") or text.startswith("!"):
        return
    
    # Parse message
    parsed = parse_message(text)
    if not parsed:
        return
    
    amount, crypto, fiat = parsed
    
    # Find valid symbol
    symbol = find_symbol(crypto)
    if not symbol:
        await update.message.reply_text(
            f"❌ Token `{crypto}` tidak ditemukan.\n"
            f"Ketik `/help` untuk info.",
            parse_mode="Markdown"
        )
        return
    
    # Get coin info
    coin_info = coins_by_symbol.get(symbol, {})
    coin_name = coin_info.get('name', symbol)
    
    # Fetch price
    price = fetch_price(symbol, fiat)
    if price is None:
        await update.message.reply_text("⚠️ Gagal ambil harga. Coba lagi sebentar.")
        return
    
    # Calculate total
    total = amount * price
    
    # Format output
    fiat_display = FIAT_DISPLAY.get(fiat, fiat.upper())
    formatted_price = format_number(price, fiat)
    formatted_total = format_number(total, fiat)
    
    # Build reply
    reply = (
        f"**💰 {amount} {symbol} = {fiat_display} {formatted_total}**\n\n"
        f"📊 1 {symbol} = {fiat_display} {formatted_price}\n"
        f"📝 {coin_name}\n"
        f"🕐 Live CryptoCompare"
    )
    
    await update.message.reply_text(reply, parse_mode="Markdown")


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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


async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    total = len(coins_by_symbol)
    help_text = (
        f"🟠 **Bantuan**\n\n"
        f"Support **{total:,}+ token**!\n\n"
        f"**Contoh:**\n"
        f"`1 btc idr` → Bitcoin ke Rupiah\n"
        f"`0.5 eth usd` → Ethereum ke Dollar\n"
        f"`10 sol idr` → Solana ke Rupiah\n"
        f"`1m pepe idr` → 1 Juta PEPE ke Rupiah\n\n"
        f"**Fiat:** IDR, USD, EUR, SGD, AUD, dll\n\n"
        f"**Commands:**\n"
        f"/start - Info bot\n"
        f"/help - Bantuan\n"
        f"/coins - Info jumlah token"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def handle_coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        print("❌ Set TELEGRAM_BOT_TOKEN!")
        exit(1)
    
    print("🚀 Bozdrop Price Bot v3 starting...")
    
    # Load coins list
    if not load_coins_from_cache():
        fetch_coins_list()
    
    # Update USD/IDR rate
    update_usd_idr_rate()
    
    print(f"✅ {len(coins_by_symbol):,} coins loaded")
    print("✅ Bot running!")
    
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
