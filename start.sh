#!/bin/bash
# 🟠 Bozdrop Price Bot — Start Script

# Set your bot token here
export TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-}"

# Check if token is set
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "❌ TELEGRAM_BOT_TOKEN not set!"
    echo ""
    echo "Cara setup:"
    echo "1. Buka @BotFather di Telegram"
    echo "2. Kirim /newbot"
    echo "3. Copy token yang dikasih"
    echo "4. Set token:"
    echo "   export TELEGRAM_BOT_TOKEN='your_token_here'"
    echo ""
    echo "Atau langsung run:"
    echo "   TELEGRAM_BOT_TOKEN='your_token' python3 bot.py"
    exit 1
fi

echo "🚀 Starting Bozdrop Price Bot..."
python3 bot.py
