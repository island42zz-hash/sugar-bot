import ast
import json
import logging
import operator
import os
import random
import time

import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from fun_content import DARES, EIGHTBALL, FACTS, JOKES, QUIZZES, RULES, TRUTHS

GROUP_CHAT_ID = os.environ.get("GROUP_CHAT_ID")  # để dùng cho /confess (tùy chọn)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("sugar-bot")

BOT_TOKEN = os.environ.get("BOT_TOKEN")
TRIGGERS_FILE = os.path.join(os.path.dirname(__file__), "triggers.json")

# Coin symbol -> CoinGecko id (dùng khi Binance không có cặp USDT), mở rộng thêm tùy ý
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

# CoinGecko hay chặn request từ server/datacenter nếu thiếu User-Agent
HTTP_HEADERS = {"User-Agent": "Mozilla/5.0 (SugarBot/1.0)"}


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
    symbol = context.args[0].upper().lstrip("$")

    # 1) Ưu tiên Binance — ổn định, free, không bị chặn từ server
    try:
        pair = f"{symbol}USDT"
        resp = requests.get(
            "https://api.binance.com/api/v3/ticker/24hr",
            params={"symbol": pair},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            price = float(data["lastPrice"])
            change = float(data["priceChangePercent"])
            arrow = "🟢" if change >= 0 else "🔴"
            await update.message.reply_text(
                f"💰 {symbol}/USDT: ${price:,.4f}\n{arrow} 24h: {change:.2f}% (nguồn: Binance)"
            )
            return
        # symbol không tồn tại trên Binance -> rơi xuống fallback CoinGecko
    except Exception:
        logger.exception("crypto binance error")
        # tiếp tục thử CoinGecko bên dưới

    # 2) Fallback: CoinGecko (cho coin nhỏ không có trên Binance)
    try:
        coin_id = COIN_MAP.get(symbol)
        if not coin_id:
            search = requests.get(
                "https://api.coingecko.com/api/v3/search",
                params={"query": symbol},
                headers=HTTP_HEADERS,
                timeout=10,
            )
            search.raise_for_status()
            coins = search.json().get("coins", [])
            if not coins:
                await update.message.reply_text(f"Không tìm thấy coin '{symbol}' 😕")
                return
            coin_id = coins[0]["id"]

        price_resp = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={
                "ids": coin_id,
                "vs_currencies": "usd",
                "include_24hr_change": "true",
            },
            headers=HTTP_HEADERS,
            timeout=10,
        )
        price_resp.raise_for_status()
        data = price_resp.json().get(coin_id)
        if not data:
            await update.message.reply_text(
                f"Không lấy được giá cho '{symbol}' — coin có thể không tồn tại hoặc API đang giới hạn 😕"
            )
            return
        usd = data.get("usd")
        change = data.get("usd_24h_change", 0)
        arrow = "🟢" if change >= 0 else "🔴"
        await update.message.reply_text(
            f"💰 {symbol}: ${usd:,.4f}\n{arrow} 24h: {change:.2f}% (nguồn: CoinGecko)"
        )
    except Exception as e:
        logger.exception("crypto coingecko error")
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


# ---------- /meme ----------
async def meme_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        resp = requests.get(
            "https://meme-api.com/gimme/cryptocurrencymemes", timeout=10
        ).json()
        url = resp.get("url")
        title = resp.get("title", "Meme")
        if url:
            await update.message.reply_photo(photo=url, caption=f"😂 {title}")
        else:
            await update.message.reply_text("Không lấy được meme lúc này, thử lại sau 😅")
    except Exception as e:
        logger.exception("meme error")
        await update.message.reply_text(f"Lỗi lấy meme: {e}")


# ---------- /joke ----------
async def joke_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🤣 {random.choice(JOKES)}")


# ---------- /fact ----------
async def fact_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"💡 {random.choice(FACTS)}")


# ---------- /8ball ----------
async def eightball_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Cú pháp: /8ball <câu hỏi>\nVD: /8ball Có nên mua BTC hôm nay?")
        return
    question = " ".join(context.args)
    await update.message.reply_text(f"🎱 {question}\n→ {random.choice(EIGHTBALL)}")


# ---------- /roll ----------
async def roll_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    spec = context.args[0] if context.args else "1d6"
    try:
        n, sides = spec.lower().split("d")
        n = int(n) if n else 1
        sides = int(sides)
        if not (1 <= n <= 20 and 2 <= sides <= 1000):
            raise ValueError
        rolls = [random.randint(1, sides) for _ in range(n)]
        total = sum(rolls)
        detail = ", ".join(str(r) for r in rolls)
        await update.message.reply_text(f"🎲 Kết quả: {detail} (tổng: {total})")
    except Exception:
        await update.message.reply_text("Cú pháp: /roll <NdM>\nVD: /roll 2d6 (tung 2 xúc xắc 6 mặt)")


# ---------- /flip ----------
async def flip_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = random.choice(["🚀 PUMP", "📉 DUMP"])
    await update.message.reply_text(f"🪙 Tung đồng xu crypto: {result}")


# ---------- /truth & /dare ----------
async def truth_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🧠 Truth: {random.choice(TRUTHS)}")


async def dare_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🔥 Dare: {random.choice(DARES)}")


# ---------- /quiz ----------
async def quiz_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question, options, correct_idx = random.choice(QUIZZES)
    await context.bot.send_poll(
        chat_id=update.effective_chat.id,
        question=f"🧩 {question}",
        options=options,
        type="quiz",
        correct_option_id=correct_idx,
        is_anonymous=True,
        open_period=30,
    )


# ---------- /confess ----------
async def confess_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Cú pháp: /confess <nội dung> — gửi ẩn danh vào group cấu hình sẵn.")
        return
    if not GROUP_CHAT_ID:
        await update.message.reply_text("Chưa cấu hình GROUP_CHAT_ID trên Railway nên chưa dùng được /confess.")
        return
    text = " ".join(context.args)
    try:
        await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=f"🙊 Confession ẩn danh:\n{text}")
        if update.effective_chat.id != int(GROUP_CHAT_ID):
            await update.message.reply_text("Đã gửi ẩn danh vào group ✅")
    except Exception as e:
        logger.exception("confess error")
        await update.message.reply_text(f"Lỗi gửi confession: {e}")


# ---------- /fng — Fear & Greed Index ----------
async def fng_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        resp = requests.get("https://api.alternative.me/fng/", timeout=10, headers=HTTP_HEADERS)
        resp.raise_for_status()
        entry = resp.json()["data"][0]
        value = int(entry["value"])
        label = entry["value_classification"]
        vi_label = {
            "Extreme Fear": "Cực kỳ sợ hãi 😱",
            "Fear": "Sợ hãi 😨",
            "Neutral": "Trung lập 😐",
            "Greed": "Tham lam 🤑",
            "Extreme Greed": "Cực kỳ tham lam 🚀",
        }.get(label, label)
        bar_filled = round(value / 10)
        bar = "🟩" * bar_filled + "⬜" * (10 - bar_filled)
        await update.message.reply_text(
            f"📊 Chỉ số Sợ hãi & Tham lam (Crypto Fear & Greed)\n"
            f"{bar}\n"
            f"{value}/100 — {vi_label}"
        )
    except Exception as e:
        logger.exception("fng error")
        await update.message.reply_text(f"Lỗi lấy chỉ số F&G: {e}")


# ---------- /top10 ----------
async def top10_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        resp = requests.get(
            "https://api.coingecko.com/api/v3/coins/markets",
            params={
                "vs_currency": "usd",
                "order": "market_cap_desc",
                "per_page": 10,
                "page": 1,
                "price_change_percentage": "24h",
            },
            headers=HTTP_HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
        coins = resp.json()
        if not coins:
            await update.message.reply_text("Không lấy được dữ liệu Top 10 lúc này 😕")
            return
        lines = ["🏆 Top 10 crypto theo vốn hóa\n"]
        for i, c in enumerate(coins, start=1):
            change = c.get("price_change_percentage_24h") or 0
            arrow = "🟢" if change >= 0 else "🔴"
            lines.append(
                f"{i}. {c['symbol'].upper()} — ${c['current_price']:,.2f} {arrow} {change:.2f}%"
            )
        await update.message.reply_text("\n".join(lines))
    except Exception as e:
        logger.exception("top10 error")
        await update.message.reply_text(f"Lỗi lấy Top 10: {e}")


# ---------- /convert ----------
async def convert_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 3:
        await update.message.reply_text(
            "Cú pháp: /convert <số lượng> <từ> <sang>\n"
            "VD: /convert 100 USD VND\nVD: /convert 0.5 BTC USDT\nVD: /convert 2000000 VND USD"
        )
        return
    try:
        amount = float(context.args[0])
    except ValueError:
        await update.message.reply_text("Số lượng không hợp lệ 😕")
        return
    from_cur = context.args[1].upper()
    to_cur = context.args[2].upper()

    try:
        usd_value = await _to_usd(amount, from_cur)
        if usd_value is None:
            await update.message.reply_text(f"Không nhận diện được đơn vị '{from_cur}' 😕")
            return
        result = await _from_usd(usd_value, to_cur)
        if result is None:
            await update.message.reply_text(f"Không nhận diện được đơn vị '{to_cur}' 😕")
            return
        await update.message.reply_text(
            f"💱 {amount:g} {from_cur} ≈ {result:,.6g} {to_cur}"
        )
    except Exception as e:
        logger.exception("convert error")
        await update.message.reply_text(f"Lỗi quy đổi: {e}")


async def _to_usd(amount: float, symbol: str):
    if symbol == "USD":
        return amount
    # thử coi là tiền pháp định qua tỷ giá USD
    rate = _get_fiat_rate(symbol)
    if rate is not None:
        return amount / rate
    # thử coi là crypto qua Binance
    price = _get_binance_price(symbol)
    if price is not None:
        return amount * price
    return None


async def _from_usd(usd_value: float, symbol: str):
    if symbol == "USD":
        return usd_value
    rate = _get_fiat_rate(symbol)
    if rate is not None:
        return usd_value * rate
    price = _get_binance_price(symbol)
    if price is not None:
        return usd_value / price
    return None


def _get_fiat_rate(symbol: str):
    try:
        resp = requests.get("https://open.er-api.com/v6/latest/USD", timeout=10)
        resp.raise_for_status()
        rates = resp.json().get("rates", {})
        return rates.get(symbol)
    except Exception:
        return None


def _get_binance_price(symbol: str):
    try:
        resp = requests.get(
            "https://api.binance.com/api/v3/ticker/price",
            params={"symbol": f"{symbol}USDT"},
            timeout=10,
        )
        if resp.status_code != 200:
            return None
        return float(resp.json()["price"])
    except Exception:
        return None


# ---------- /ping ----------
async def ping_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start = time.monotonic()
    msg = await update.message.reply_text("🏓 Đang đo...")
    elapsed_ms = (time.monotonic() - start) * 1000
    await msg.edit_text(f"🏓 Pong! {elapsed_ms:.0f}ms")


# ---------- /rules ----------
async def rules_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(RULES)


# ---------- Chào thành viên mới ----------
async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        if member.is_bot:
            continue
        name = member.first_name or "bạn"
        await update.message.reply_text(
            f"🎉 Chào mừng {name} đã tham gia group!\n\n"
            f"Gõ /help để xem bot làm được gì — thời tiết, giá crypto, meme, "
            f"quiz, truth or dare... đủ cả 😄\n"
            f"Gõ /rules để xem nội quy group nhé."
        )


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


# ---------- /start & /help — menu nút bấm ----------
MAIN_MENU = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("🔧 Công cụ", callback_data="menu_tools")],
        [InlineKeyboardButton("📈 Thị trường", callback_data="menu_market")],
        [InlineKeyboardButton("🎉 Vui / Giao lưu", callback_data="menu_fun")],
        [InlineKeyboardButton("📜 Nội quy", callback_data="menu_rules")],
    ]
)

MENU_TEXT = {
    "menu_tools": (
        "🔧 Công cụ\n\n"
        "/weather <city> — thời tiết\n"
        "/translate <text> — dịch nhanh\n"
        "/calc <expression> — máy tính\n"
        "/short <url> — rút gọn link\n"
        "/convert <số> <từ> <sang> — quy đổi tiền tệ/crypto\n"
        "/ping — đo tốc độ phản hồi bot"
    ),
    "menu_market": (
        "📈 Thị trường\n\n"
        "/crypto <coin> — giá crypto real-time\n"
        "/top10 — Top 10 coin theo vốn hóa\n"
        "/fng — Chỉ số Sợ hãi & Tham lam"
    ),
    "menu_fun": (
        "🎉 Vui / Giao lưu\n\n"
        "/meme — meme crypto ngẫu nhiên\n"
        "/joke — joke crypto/kinh doanh\n"
        "/fact — fact thú vị\n"
        "/8ball <câu hỏi> — quả cầu tiên tri\n"
        "/roll <NdM> — tung xúc xắc\n"
        "/flip — tung xu pump/dump\n"
        "/truth, /dare — truth or dare\n"
        "/quiz — trivia crypto (poll 30s)\n"
        "/confess <nội dung> — confession ẩn danh"
    ),
    "menu_rules": RULES,
}


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Sugar bot đã sẵn sàng!\n\nBấm 1 mục bên dưới để xem lệnh, hoặc gõ /help bất cứ lúc nào.",
        reply_markup=MAIN_MENU,
    )


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = MENU_TEXT.get(query.data)
    if text:
        await query.edit_message_text(text, reply_markup=MAIN_MENU)


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
    app.add_handler(CommandHandler("convert", convert_cmd))
    app.add_handler(CommandHandler("ping", ping_cmd))
    app.add_handler(CommandHandler("top10", top10_cmd))
    app.add_handler(CommandHandler("fng", fng_cmd))
    app.add_handler(CommandHandler("rules", rules_cmd))
    app.add_handler(CommandHandler("meme", meme_cmd))
    app.add_handler(CommandHandler("joke", joke_cmd))
    app.add_handler(CommandHandler("fact", fact_cmd))
    app.add_handler(CommandHandler("8ball", eightball_cmd))
    app.add_handler(CommandHandler("roll", roll_cmd))
    app.add_handler(CommandHandler("flip", flip_cmd))
    app.add_handler(CommandHandler("truth", truth_cmd))
    app.add_handler(CommandHandler("dare", dare_cmd))
    app.add_handler(CommandHandler("quiz", quiz_cmd))
    app.add_handler(CommandHandler("confess", confess_cmd))
    app.add_handler(CallbackQueryHandler(menu_callback, pattern="^menu_"))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_reply))

    logger.info("Bot đang chạy...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
