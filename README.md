# 🟠 Bozdrop Price Bot — Setup Guide

## Cara Setup

### 1. Buat Bot di Telegram
```
1. Buka @BotFather di Telegram
2. Kirim /newbot
3. Nama: Bozdrop Price Bot
4. Username: bozdrop_price_bot (atau apa aja yang available)
5. Copy TOKEN yang dikasih BotFather
```

### 2. Set Token
```bash
export TELEGRAM_BOT_TOKEN="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
```

### 3. Run Bot
```bash
cd /Users/dannboz/bozdrop-price-bot
python3 bot.py
```

### 4. Add Bot ke Grup
```
1. Buka grup Telegram
2. Tambahkan bot sebagai member
3. Kasih permission "Read Messages"
4. Done! User bisa ketik "1 btc idr" langsung dapet harga
```

## Format Pesan
```
1 btc idr      → 1 Bitcoin = Rp 1,542,360,000
0.5 eth usd    → 0.5 ETH = $1,847.25
10 sol idr     → 10 SOL = Rp 18,450,000
```

## Commands
- `/start` - Welcome message
- `/help` - Daftar crypto & fiat yang supported

## Supported Crypto (50+)
BTC, ETH, BNB, SOL, ADA, XRP, DOGE, AVAX, MATIC, DOT, LINK, UNI, ATOM, NEAR, ARB, OP, SUI, APT, TIA, SEI, WIF, BONK, PEPE, FLOKI, SHIB, TRX, ETC, LTC, BCH, XLM, ALGO, VET, ICP, FTM, GRT, AAVE, MKR, LDO, RAY, JUP, PYTH, JTO, W, ENA, PENDLE, ONDO, PIXEL, NFT, CAKE, SFP, 1INCH, CHZ, SAND, MANA, AXS, GAL, BLUR, ENS, CRV, SNX, COMP, YFI, SUSHI

## Supported Fiat (16+)
IDR, USD, EUR, GBP, JPY, SGD, AUD, CAD, CNY, INR, KRW, THB, PHP, MYR, VND, RUB, TRY, BRL, MXN, ZAR, AED, HKD, TWD

## Notes
- Price source: CoinGecko (free, no API key)
- Cache: 30 detik per pair (hemat request)
- Bisa running 24/7 kalau pakai VPS/Heroku
