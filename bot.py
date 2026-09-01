import ast
import json
import logging
import operator
import os

import requests
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("sugar-bot")

BOT_TOKEN = os.environ.get("BOT_TOKEN")
TRIGGERS_FILE = os.path.join(os.path.dirname(__file__), "triggers.json")

# Coin symbol -> CoinGecko id, mở rộng thêm tùy ý
COIN_MAP = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "TON": "the-open-network",
    "USDT": "tether",
    "USDC": "usd-coin",
    "BNB": "binancecoin",
    "SOL": "solana",
    "XRP": "ripple",
    "DOGE": "dogecoin",
    "ADA": "cardano",
    "TRX": "tron",
    "SUI": "sui",
    "OKB": "okb",
}


def load_triggers() -> dict:
    try:
        with open(TRIGGERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


# ---------- /weather ----------
async def weather_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Cú pháp: /weather <tên thành phố>\nVD: /weather Phu Quoc")
        return
    city = " ".join(context.args)
    try:
        geo = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1, "language": "vi"},
            timeout=10,
        ).json()
        results = geo.get("results")
        if not results:
            await update.message.reply_text(f"Không tìm thấy thành phố '{city}' 😕")
            return
        loc = results[0]
        lat, lon = loc["latitude"], loc["longitude"]
        name = loc.get("name", city)
        country = loc.get("country", "")

        wx = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
            },
            timeout=10,
        ).json()
        cur = wx.get("current", {})
        temp = cur.get("temperature_2m")
        humidity = cur.get("relative_humidity_2m")
        wind = cur.get("wind_speed_10m")
        code = cur.get("weather_code")

        desc = WEATHER_CODES.get(code, "Không rõ")
        msg = (
            f"🌤 Thời tiết {name}, {country}\n"
            f"🌡 Nhiệt độ: {temp}°C\n"
            f"💧 Độ ẩm: {humidity}%\n"
            f"💨 Gió: {wind} km/h\n"
            f"☁️ Tình trạng: {desc}"
        )
        await update.message.reply_text(msg)
    except Exception as e:
        logger.exception("weather error")
        await update.message.reply_text(f"Lỗi lấy thời tiết: {e}")


WEATHER_CODES = {
    0: "Trời quang",
    1: "Ít mây",
    2: "Mây rải rác",
    3: "Nhiều mây",
    45: "Sương mù",
    48: "Sương mù đóng băng",
    51: "Mưa phùn nhẹ",
    53: "Mưa phùn",
    55: "Mưa phùn dày",
    61: "Mưa nhỏ",
    63: "Mưa vừa",
    65: "Mưa to",
    71: "Tuyết nhẹ",
    73: "Tuyết vừa",
    75: "Tuyết to",
    80: "Mưa rào nhẹ",
    81: "Mưa rào vừa",
    82: "Mưa rào to",
    95: "Dông",
    96: "Dông kèm mưa đá",
    99: "Dông kèm mưa đá to",
}


# ---------- /crypto ----------
async def crypto_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Cú pháp: /crypto <coin>\nVD: /crypto BTC")
        return
    symbol = context.args[0].upper()
    coin_id = COIN_MAP.get(symbol)
    try:
        if not coin_id:
            # fallback: search CoinGecko
            search = requests.get(
                "https://api.coingecko.com/api/v3/search",
                params={"query": symbol},
                timeout=10,
            ).json()
            coins = search.get("coins", [])
            if not coins:
                await update.message.reply_text(f"Không tìm thấy coin '{symbol}' 😕")
                return
            coin_id = coins[0]["id"]

        price = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={
                "ids": coin_id,
                "vs_currencies": "usd",
                "include_24hr_change": "true",
            },
            timeout=10,
        ).json()
        data = price.get(coin_id)
        if not data:
            await update.message.reply_text(f"Không lấy được giá cho '{symbol}' 😕")
            return
        usd = data.get("usd")
        change = data.get("usd_24h_change", 0)
        arrow = "🟢" if change >= 0 else "🔴"
        await update.message.reply_text(
            f"💰 {symbol}: ${usd:,.4f}\n{arrow} 24h: {change:.2f}%"
        )
    except Exception as e:
        logger.exception("crypto error")
        await update.message.reply_text(f"Lỗi lấy giá crypto: {e}")


# ---------- /translate ----------
async def translate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Cú pháp: /translate <text> (auto detect, dịch sang Việt)\n"
            "Hoặc: /translate <mã ngôn ngữ đích> <text>\nVD: /translate en xin chào"
        )
        return

    target = "vi"
    words = context.args
    possible_lang = words[0].lower()
    if len(possible_lang) == 2 and len(words) > 1:
        target = possible_lang
        text = " ".join(words[1:])
    else:
        text = " ".join(words)

    try:
        resp = requests.get(
            "https://translate.googleapis.com/translate_a/single",
            params={
                "client": "gtx",
                "sl": "auto",
                "tl": target,
                "dt": "t",
                "q": text,
            },
            timeout=10,
        ).json()
        translated = "".join(chunk[0] for chunk in resp[0])
        await update.message.reply_text(f"🌐 {translated}")
    except Exception as e:
        logger.exception("translate error")
        await update.message.reply_text(f"Lỗi dịch: {e}")


# ---------- /calc ----------
SAFE_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def safe_eval(node):
    if isinstance(node, ast.Expression):
        return safe_eval(node.body)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Chỉ hỗ trợ số")
    if isinstance(node, ast.BinOp) and type(node.op) in SAFE_OPS:
        return SAFE_OPS[type(node.op)](safe_eval(node.left), safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in SAFE_OPS:
        return SAFE_OPS[type(node.op)](safe_eval(node.operand))
    raise ValueError("Biểu thức không hợp lệ")


async def calc_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Cú pháp: /calc <biểu thức>\nVD: /calc (12+8)*3/2")
        return
    expr = " ".join(context.args)
    try:
        tree = ast.parse(expr, mode="eval")
        result = safe_eval(tree)
        await update.message.reply_text(f"🧮 {expr} = {result}")
    except Exception:
        await update.message.reply_text("Biểu thức không hợp lệ 😕 (chỉ hỗ trợ + - * / // % **)")


# ---------- /short ----------
async def short_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Cú pháp: /short <url>\nVD: /short https://example.com/long-link")
        return
    url = context.args[0]
    try:
        resp = requests.get(
            "https://is.gd/create.php",
            params={"format": "simple", "url": url},
            timeout=10,
        )
        short_url = resp.text.strip()
        if short_url.startswith("http"):
            await update.message.reply_text(f"🔗 {short_url}")
        else:
            await update.message.reply_text(f"Lỗi rút gọn link: {short_url}")
    except Exception as e:
        logger.exception("short error")
        await update.message.reply_text(f"Lỗi rút gọn link: {e}")


# ---------- Auto-reply theo keyword ----------
async def auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    text = update.message.text.lower()
    triggers = load_triggers()
    for keyword, reply in triggers.items():
        if keyword.lower() in text:
            await update.message.reply_text(reply)
            return


# ---------- /start & /help ----------
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Sugar bot đã sẵn sàng!\n\n"
        "/weather <city> — thời tiết\n"
        "/crypto <coin> — giá crypto\n"
        "/translate <text> — dịch nhanh\n"
        "/calc <expression> — máy tính\n"
        "/short <url> — rút gọn link\n\n"
        "Trong group, bot còn tự động reply theo keyword (sửa trong triggers.json)."
    )


def main():
    if not BOT_TOKEN:
        raise RuntimeError("Thiếu biến môi trường BOT_TOKEN")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", start_cmd))
    app.add_handler(CommandHandler("weather", weather_cmd))
    app.add_handler(CommandHandler("crypto", crypto_cmd))
    app.add_handler(CommandHandler("translate", translate_cmd))
    app.add_handler(CommandHandler("calc", calc_cmd))
    app.add_handler(CommandHandler("short", short_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_reply))

    logger.info("Bot đang chạy...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
