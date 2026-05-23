#!/usr/bin/env python3
"""🟠 Bozdrop Price Bot - Simple Version"""
import os
import sys
import re
import requests
from telegram import Update, ForceReply
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Token dari environment variable
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
if not TOKEN:
    print("ERROR: Set TELEGRAM_BOT_TOKEN!")
    sys.exit(1)

# ==================== COMMANDS ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🟠 Bozdrop Price Bot\n\n"
        "Cara pakai:\n"
        "1 btc idr\n"
        "0.5 eth usd\n"
        "10 sol idr\n\n"
        "Bot otomatis balas harga!"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🟠 Bantuan\n\n"
        "Format: [jumlah] [crypto] [fiat]\n"
        "Contoh:\n"
        "1 btc idr → Bitcoin ke Rupiah\n"
        "0.5 eth usd → Ethereum ke Dollar\n"
        "10 sol idr → Solana ke Rupiah\n\n"
        "Support: BTC, ETH, SOL, BNB, XRP, DOGE, ADA, AVAX, MATIC, dll"
    )

# ==================== PRICE FETCH ====================

def get_price(symbol: str, fiat: str):
    """Fetch price from CryptoCompare API"""
    try:
        url = f"https://min-api.cryptocompare.com/data/price?fsym={symbol}&tsyms={fiat}"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if fiat in data:
            return float(data[fiat])
    except:
        pass
    return None

def format_price(num: float, fiat: str) -> str:
    """Format number based on currency"""
    fiat = fiat.lower()
    if fiat == "idr":
        return f"Rp {int(num):,}".replace(",", ".")
    elif num < 0.0001:
        return f"${num:.10f}"
    elif num < 1:
        return f"${num:.6f}"
    else:
        return f"${num:,.2f}"

# ==================== MESSAGE HANDLER ====================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages"""
    if not update.message or not update.message.text:
        return
    
    text = update.message.text.strip().lower()
    
    # Skip commands
    if text.startswith("/") or text.startswith("!"):
        return
    
    # Parse: "1 btc idr" or "0.5 eth usd"
    pattern = r"^(\d+(?:\.\d+)?)\s*([a-z0-9]+)\s+([a-z]{3,4})$"
    match = re.match(pattern, text)
    
    if not match:
        return
    
    amount = float(match.group(1))
    crypto = match.group(2).upper()
    fiat = match.group(3).upper()
    
    # Fetch price
    price = get_price(crypto, fiat)
    
    if price is None:
        await update.message.reply_text(f"⚠️ Gagal ambil harga {crypto}/{fiat}")
        return
    
    # Calculate total
    total = amount * price
    
    # Format output
    if fiat == "IDR":
        formatted_price = f"Rp {int(price):,}".replace(",", ".")
        formatted_total = f"Rp {int(total):,}".replace(",", ".")
    else:
        if price < 0.0001:
            formatted_price = f"${price:.10f}"
            formatted_total = f"${total:.10f}"
        elif price < 1:
            formatted_price = f"${price:.6f}"
            formatted_total = f"${total:.6f}"
        else:
            formatted_price = f"${price:,.2f}"
            formatted_total = f"${total:,.2f}"
    
    reply = f"**💰 {amount} {crypto} = {formatted_total}**\n\n"
    reply += f"📊 1 {crypto} = {formatted_price}\n"
    reply += f"🕐 Live Price"
    
    await update.message.reply_text(reply, parse_mode="Markdown")

# ==================== MAIN ====================

def main():
    print("🚀 Bozdrop Price Bot starting...")
    
    # Create application
    app = Application.builder().token(TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ Bot running!")
    
    # Start polling
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
