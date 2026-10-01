#!/usr/bin/env python3
"""Sugar Super Bot — thuần Việt, trả lời lệnh / và nút nhóm, có thẻ ảnh.

Chạy:
  TELEGRAM_BOT_TOKEN=123:abc python3 scripts/bot.py
"""

from __future__ import annotations

import ast
import json
import operator
import os
import random
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

import cards  # noqa: E402

COPY = json.loads((ROOT / "assets" / "copy.json").read_text(encoding="utf-8"))
FUN = json.loads((ROOT / "assets" / "fun.json").read_text(encoding="utf-8"))

BUTTONS = ["Công cụ", "Thị trường", "Vui / Giao lưu", "Nội quy"]
KEYBOARD = [["Công cụ", "Thị trường"], ["Vui / Giao lưu", "Nội quy"]]

MENU = [
    ("batdau", "Mở bot và hiện nút"),
    ("trogiup", "Xem bốn nhóm lệnh"),
    ("gia", "Giá tiền mã hóa kèm ảnh"),
    ("xephang", "Mười mã vốn hóa lớn"),
    ("socamxuc", "Chỉ số sợ hãi và tham lam"),
    ("chungkhoan", "Chỉ số chứng khoán thế giới"),
    ("tintuc", "Tin Việt Nam, làm ăn hoặc tiền mã hóa"),
    ("thoittiet", "Thời tiết theo thành phố"),
    ("dich", "Dịch nhanh"),
    ("tinh", "Máy tính"),
    ("rutgon", "Rút gọn liên kết"),
    ("doitien", "Đổi tiền"),
    ("tocdo", "Đo tốc độ phản hồi"),
    ("anhche", "Ảnh chế thị trường"),
    ("caucuo", "Câu cười"),
    ("suthat", "Sự thật ngắn"),
    ("boi", "Quả cầu trả lời"),
    ("xucxac", "Tung xúc xắc"),
    ("tungxu", "Tung đồng xu"),
    ("sukien", "Câu hỏi sự thật"),
    ("thuthach", "Thử thách"),
    ("dovui", "Đố vui, bình chọn 30 giây"),
    ("tamtinh", "Tâm sự ẩn với nhóm"),
    ("thamthuy", "Câu nói thâm"),
    ("treu", "Trêu nhẹ thị trường"),
    ("bong", "Hiện một câu rồi biến"),
    ("noiquy", "Nội quy nhóm"),
]

ALIASES = {
    "start": "batdau",
    "help": "trogiup",
    "ping": "tocdo",
    "price": "gia",
    "crypto": "gia",
    "top10": "xephang",
    "fng": "socamxuc",
    "stocks": "chungkhoan",
    "news": "tintuc",
    "weather": "thoittiet",
    "translate": "dich",
    "calc": "tinh",
    "short": "rutgon",
    "convert": "doitien",
    "meme": "anhche",
    "joke": "caucuo",
    "fact": "suthat",
    "8ball": "boi",
    "roll": "xucxac",
    "flip": "tungxu",
    "truth": "sukien",
    "dare": "thuthach",
    "quiz": "dovui",
    "confess": "tamtinh",
    "roast": "treu",
    "rules": "noiquy",
    "ghost": "bong",
}

GROUPS = {
    "Công cụ": [
        "/thoittiet <thành phố> — thời tiết",
        "/dich <văn bản> — dịch nhanh",
        "/tinh <phép tính> — máy tính",
        "/rutgon <liên kết> — rút gọn link",
        "/doitien <số> <từ> <sang> — đổi tiền",
        "/tocdo — tốc độ phản hồi",
    ],
    "Thị trường": [
        "/gia <mã> — giá kèm ảnh, thử /gia btc",
        "/xephang — mười mã theo vốn hóa",
        "/socamxuc — sợ hãi và tham lam",
        "/chungkhoan — Mỹ và Việt Nam",
        "/tintuc [viet|lam|tien] — tin",
    ],
    "Vui / Giao lưu": [
        "/anhche — ảnh chế",
        "/caucuo — câu cười",
        "/suthat — sự thật ngắn",
        "/boi <câu hỏi> — quả cầu",
        "/xucxac [2d6] — xúc xắc",
        "/tungxu — đồng xu",
        "/sukien — sự thật",
        "/thuthach — thử thách",
        "/dovui — đố vui",
        "/tamtinh <nội dung> — tâm sự ẩn danh",
        "/thamthuy — câu nói thâm",
        "/treu — trêu nhẹ thị trường",
        "/bong — hiện một câu rồi biến",
    ],
}

OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


class Out:
    def __init__(self, text: str, photo: bytes | None = None, poll: dict | None = None, anonymous: bool = False):
        self.text = text
        self.photo = photo
        self.poll = poll
        self.anonymous = anonymous


def extract_command(text: str, bot_username: str | None) -> tuple[str, str] | None:
    if not text or not text.strip().startswith("/"):
        return None
    head, _, rest = text.strip().partition(" ")
    token = head[1:]
    name, sep, target = token.partition("@")
    name = name.lower()
    if not name or not re.fullmatch(r"[a-z0-9_]+", name):
        return None
    if sep and bot_username and target.lower() != bot_username.lower():
        return None
    return ALIASES.get(name, name), rest.strip()


def http_json(url: str, timeout: int = 12) -> dict | list:
    req = urllib.request.Request(url, headers={"User-Agent": "SugarBot/1.0", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def http_text(url: str, timeout: int = 12) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "SugarBot/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def money(value: float, digits: int = 2) -> str:
    sign = "-" if value < 0 else ""
    raw = f"{abs(value):,.{digits}f}"
    return sign + raw.replace(",", "X").replace(".", ",").replace("X", ".")


def safe_calc(expr: str) -> float:
    tree = ast.parse(expr, mode="eval")

    def walk(node):
        if isinstance(node, ast.Expression):
            return walk(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.BinOp) and type(node.op) in OPS:
            return OPS[type(node.op)](walk(node.left), walk(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in OPS:
            return OPS[type(node.op)](walk(node.operand))
        raise ValueError("bad")

    return walk(tree)


def fng_label(score: int) -> str:
    if score <= 24:
        return "Sợ hãi cực độ"
    if score <= 44:
        return "Sợ hãi"
    if score <= 55:
        return "Trung lập"
    if score <= 74:
        return "Tham lam"
    return "Tham lam cực độ"


class CommandRouter:
    def __init__(self, rng: random.Random | None = None, online: bool = True):
        self.rng = rng or random.Random()
        self.online = online
        self.handlers = {
            "batdau": self.cmd_start,
            "trogiup": self.cmd_help,
            "noiquy": self.cmd_rules,
            "tocdo": self.cmd_ping,
            "gia": self.cmd_price,
            "xephang": self.cmd_rank,
            "socamxuc": self.cmd_mood,
            "chungkhoan": self.cmd_stocks,
            "tintuc": self.cmd_news,
            "thoittiet": self.cmd_weather,
            "dich": self.cmd_translate,
            "tinh": self.cmd_calc,
            "rutgon": self.cmd_short,
            "doitien": self.cmd_convert,
            "anhche": self.cmd_meme,
            "caucuo": self.cmd_joke,
            "suthat": self.cmd_fact,
            "boi": self.cmd_ball,
            "xucxac": self.cmd_roll,
            "tungxu": self.cmd_flip,
            "sukien": self.cmd_truth,
            "thuthach": self.cmd_dare,
            "dovui": self.cmd_quiz,
            "tamtinh": self.cmd_confess,
            "thamthuy": self.cmd_quote,
            "treu": self.cmd_roast,
            "bong": self.cmd_ghost,
        }

    def reply(self, text: str, ctx: dict | None = None) -> Out | None:
        ctx = ctx or {}
        stripped = (text or "").strip()
        if stripped in GROUPS:
            return Out(self.group_text(stripped))
        if stripped == "Nội quy":
            return self.cmd_rules("", ctx)
        parsed = extract_command(stripped, ctx.get("bot_username"))
        if not parsed:
            return None
        name, args = parsed
        handler = self.handlers.get(name)
        if not handler:
            return Out(COPY["unknown"])
        return handler(args, ctx)

    def group_text(self, name: str) -> str:
        lines = [name] + GROUPS[name]
        if name == "Thị trường":
            lines.append(COPY["market_note"])
        return "\n".join(lines)

    def cmd_start(self, args: str, ctx: dict) -> Out:
        return Out(COPY["ready"], photo=cards.welcome_card())

    def cmd_help(self, args: str, ctx: dict) -> Out:
        return Out(COPY["ready"])

    def cmd_rules(self, args: str, ctx: dict) -> Out:
        lines = [COPY["rules_title"]]
        for i, rule in enumerate(COPY["rules"], 1):
            lines.append(f"{i}. {rule}")
        return Out("\n".join(lines))

    def cmd_ping(self, args: str, ctx: dict) -> Out:
        lag = ctx.get("lag_ms")
        if lag is None:
            return Out("Còn đây.")
        return Out(f"Còn đây. Lệnh tới sau {lag} mili giây.")

    def cmd_meme(self, args: str, ctx: dict) -> Out:
        if self.online:
            fetched = self.fetch_meme()
            if fetched:
                return fetched
        line = self.rng.choice(FUN["meme_lines"])
        return Out(line, photo=cards.meme_card(line))

    def fetch_meme(self) -> Out | None:
        subs = ("cryptocurrencymemes", "CryptoMemes", "memes")
        for _ in range(3):
            sub = self.rng.choice(subs)
            try:
                data = http_json(f"https://meme-api.com/gimme/{sub}")
                if data.get("nsfw") or data.get("spoiler"):
                    continue
                url = data.get("url") or ""
                if not url.lower().split("?")[0].endswith((".jpg", ".jpeg", ".png", ".webp")):
                    continue
                req = urllib.request.Request(url, headers={"User-Agent": "SugarBot/1.0"})
                with urllib.request.urlopen(req, timeout=20) as resp:
                    blob = resp.read()
                if not 1000 <= len(blob) <= 8_000_000:
                    continue
            except Exception:
                continue
            title = (data.get("title") or "Ảnh chế").strip()
            source = data.get("subreddit") or sub
            return Out(f"{title}\nNguồn: {source}", photo=blob)
        return None

    def cmd_joke(self, args: str, ctx: dict) -> Out:
        return Out(self.rng.choice(FUN["jokes"]))

    def cmd_fact(self, args: str, ctx: dict) -> Out:
        return Out(self.rng.choice(FUN["facts"]))

    def cmd_quote(self, args: str, ctx: dict) -> Out:
        return Out(self.rng.choice(FUN["quotes"]))

    def cmd_ball(self, args: str, ctx: dict) -> Out:
        if not args:
            return Out("Đặt câu hỏi sau lệnh. Ví dụ: /boi tuần này nên đứng ngoài không?")
        return Out(f"“{args}”\n{self.rng.choice(FUN['eightball'])}")

    def cmd_roll(self, args: str, ctx: dict) -> Out:
        spec = args or "1d6"
        match = re.fullmatch(r"(\d{1,2})d(\d{1,3})", spec.lower())
        if not match:
            return Out(COPY["bad_dice"])
        count, sides = int(match.group(1)), int(match.group(2))
        if not 1 <= count <= 20 or not 2 <= sides <= 100:
            return Out(COPY["bad_dice"])
        rolls = [self.rng.randint(1, sides) for _ in range(count)]
        return Out(f"Xúc xắc {count}d{sides}: {', '.join(map(str, rolls))}. Tổng {sum(rolls)}.")

    def cmd_flip(self, args: str, ctx: dict) -> Out:
        return Out("Ngửa — cửa tăng." if self.rng.random() < 0.5 else "Sấp — cửa giảm.")

    def cmd_truth(self, args: str, ctx: dict) -> Out:
        return Out("Sự thật: " + self.rng.choice(FUN["truths"]))

    def cmd_dare(self, args: str, ctx: dict) -> Out:
        return Out("Thử thách: " + self.rng.choice(FUN["dares"]))

    def cmd_quiz(self, args: str, ctx: dict) -> Out:
        item = self.rng.choice(FUN["quizzes"])
        return Out(
            item["q"],
            poll={"question": item["q"], "options": item["options"], "correct": item["correct"], "open_period": 30},
        )

    def cmd_confess(self, args: str, ctx: dict) -> Out:
        if not args:
            return Out(COPY["need_confess"])
        return Out(f"Tâm sự ẩn danh:\n{args[:800]}", anonymous=True)

    def cmd_roast(self, args: str, ctx: dict) -> Out:
        return Out("Thị trường không cần bị trêu. Caption lãi lỗ mới cần bị cắt một nửa.")

    def cmd_ghost(self, args: str, ctx: dict) -> Out:
        line = args[:180] if args else self.rng.choice(FUN["ghost"])
        return Out(line, photo=cards.ghost_card(line), anonymous=True)

    def cmd_calc(self, args: str, ctx: dict) -> Out:
        if not args:
            return Out(COPY["need_expr"])
        try:
            value = safe_calc(args.replace(",", "."))
        except Exception:
            return Out(COPY["bad_expr"])
        return Out(f"{args} = {money(value, 4).rstrip('0').rstrip(',')}")

    def cmd_price(self, args: str, ctx: dict) -> Out:
        if not args:
            return Out(COPY["need_coin"])
        if not self.online:
            return Out("Đang tắt mạng trong bản thử.")
        symbol = args.split()[0].lower()
        try:
            found = http_json(f"https://api.coingecko.com/api/v3/search?query={urllib.parse.quote(symbol)}")
            coins = found.get("coins") or []
            match = next((c for c in coins if c.get("symbol", "").lower() == symbol), coins[0] if coins else None)
            if not match:
                return Out(f"Không thấy mã {symbol}.")
            data = http_json(
                "https://api.coingecko.com/api/v3/simple/price"
                f"?ids={match['id']}&vs_currencies=usd,vnd&include_24hr_change=true"
            )[match["id"]]
        except Exception:
            return Out(COPY["source_fail"])
        change = float(data.get("usd_24h_change") or 0)
        usd = f"{money(float(data['usd']))} USD"
        vnd = f"{money(float(data['vnd']), 0)} đ"
        arrow = f"{'+' if change >= 0 else ''}{money(change)}% trong 24 giờ"
        text = f"{match['name']} ({match['symbol'].upper()})\n{usd}\n{vnd}\n{arrow}\n{COPY['market_note']}"
        photo = cards.price_card(match["name"], match["symbol"], usd, vnd, arrow, change >= 0)
        return Out(text, photo=photo)

    def cmd_rank(self, args: str, ctx: dict) -> Out:
        if not self.online:
            return Out("Đang tắt mạng trong bản thử.")
        try:
            rows = http_json(
                "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=10&page=1"
            )
        except Exception:
            return Out(COPY["source_fail"])
        lines = ["Mười mã vốn hóa lớn"]
        card_rows = []
        for i, coin in enumerate(rows, 1):
            change = float(coin.get("price_change_percentage_24h") or 0)
            line = f"{i}. {coin['symbol'].upper()}  {money(float(coin['current_price']))} USD  {money(change)}%"
            lines.append(line)
            card_rows.append(line)
        lines.append(COPY["market_note"])
        return Out("\n".join(lines), photo=cards.list_card("Vốn hóa", card_rows, "Nguồn công khai · không phải lời khuyên"))

    def cmd_mood(self, args: str, ctx: dict) -> Out:
        if not self.online:
            return Out("Đang tắt mạng trong bản thử.")
        try:
            data = http_json("https://api.alternative.me/fng/?limit=1")["data"][0]
            score = int(data["value"])
        except Exception:
            return Out(COPY["source_fail"])
        label = fng_label(score)
        return Out(
            f"Sợ hãi và tham lam: {score}/100 — {label}.\n{COPY['market_note']}",
            photo=cards.mood_card(score, label),
        )

    def cmd_stocks(self, args: str, ctx: dict) -> Out:
        if not self.online:
            return Out("Đang tắt mạng trong bản thử.")
        symbols = [("^spx", "S&P 500"), ("^dji", "Dow Jones"), ("^ndq", "Nasdaq"), ("^vnindex", "VN-Index")]
        lines = ["Chỉ số"]
        card_rows = []
        for symbol, label in symbols:
            try:
                raw = http_text(f"https://stooq.com/q/l/?s={urllib.parse.quote(symbol)}&f=sd2t2c&h&e=csv")
                parts = raw.strip().splitlines()[-1].split(",")
                price, change = parts[1], parts[2] if len(parts) > 2 else ""
                line = f"{label}: {price} ({change})"
            except Exception:
                line = f"{label}: chưa lấy được"
            lines.append(line)
            card_rows.append(line)
        lines.append(COPY["market_note"])
        return Out("\n".join(lines), photo=cards.list_card("Chứng khoán", card_rows, "Nguồn công khai · có độ trễ"))

    def cmd_news(self, args: str, ctx: dict) -> Out:
        if not self.online:
            return Out("Đang tắt mạng trong bản thử.")
        key = (args or "viet").split()[0].lower()
        feeds = {
            "viet": "https://vnexpress.net/rss/tin-moi-nhat.rss",
            "lam": "https://vnexpress.net/rss/kinh-doanh.rss",
            "tien": "https://vnexpress.net/rss/kinh-doanh.rss",
            "vn": "https://vnexpress.net/rss/tin-moi-nhat.rss",
            "kinhdoanh": "https://vnexpress.net/rss/kinh-doanh.rss",
            "crypto": "https://vnexpress.net/rss/so-hoa.rss",
        }
        url = feeds.get(key, feeds["viet"])
        try:
            root = ET.fromstring(http_text(url))
            titles = [node.text.strip() for node in root.findall(".//item/title") if node.text][:5]
        except Exception:
            return Out(COPY["source_fail"])
        if not titles:
            return Out("Nguồn tin chưa có mục mới.")
        return Out("Tin mới:\n" + "\n".join(f"• {title}" for title in titles))

    def cmd_weather(self, args: str, ctx: dict) -> Out:
        if not args:
            return Out(COPY["need_city"])
        if not self.online:
            return Out("Đang tắt mạng trong bản thử.")
        try:
            geo = http_json(
                "https://geocoding-api.open-meteo.com/v1/search?count=1&language=vi&name="
                + urllib.parse.quote(args)
            )
            place = (geo.get("results") or [None])[0]
            if not place:
                return Out(f"Không thấy thành phố {args}.")
            forecast = http_json(
                "https://api.open-meteo.com/v1/forecast?current=temperature_2m,weather_code"
                f"&timezone=auto&latitude={place['latitude']}&longitude={place['longitude']}"
            )
            temp = forecast["current"]["temperature_2m"]
        except Exception:
            return Out(COPY["source_fail"])
        name = place.get("name") or args
        return Out(f"{name}: {money(float(temp), 1)} °C hiện tại.")

    def cmd_translate(self, args: str, ctx: dict) -> Out:
        if not args:
            return Out(COPY["need_text"])
        if not self.online:
            return Out("Đang tắt mạng trong bản thử.")
        pair = "en|vi" if re.search(r"[A-Za-z]", args) and not re.search(r"[ăâêôơưáàảãạ]", args.lower()) else "vi|en"
        try:
            data = http_json(
                "https://api.mymemory.translated.net/get?q="
                + urllib.parse.quote(args[:400])
                + "&langpair="
                + pair
            )
            text = data["responseData"]["translatedText"]
        except Exception:
            return Out(COPY["source_fail"])
        return Out(text)

    def cmd_short(self, args: str, ctx: dict) -> Out:
        if not args.startswith("http://") and not args.startswith("https://"):
            return Out(COPY["need_url"])
        if not self.online:
            return Out("Đang tắt mạng trong bản thử.")
        try:
            short = http_text("https://is.gd/create.php?format=simple&url=" + urllib.parse.quote(args, safe="")).strip()
        except Exception:
            return Out(COPY["source_fail"])
        if not short.startswith("http"):
            return Out(COPY["source_fail"])
        return Out(short)

    def cmd_convert(self, args: str, ctx: dict) -> Out:
        parts = args.split()
        if len(parts) != 3:
            return Out(COPY["need_convert"])
        if not self.online:
            return Out("Đang tắt mạng trong bản thử.")
        amount, src, dst = parts
        try:
            number = float(amount.replace(".", "").replace(",", ".")) if "," in amount else float(amount)
            data = http_json(
                f"https://api.frankfurter.app/latest?amount={number}&from={src.upper()}&to={dst.upper()}"
            )
            value = data["rates"][dst.upper()]
        except Exception:
            return Out("Chưa đổi được cặp này. Dùng mã tiền tệ, ví dụ usd vnd.")
        return Out(f"{money(number)} {src.upper()} = {money(float(value))} {dst.upper()}")


def reply_markup() -> dict:
    return {
        "keyboard": [[{"text": item} for item in row] for row in KEYBOARD],
        "resize_keyboard": True,
        "is_persistent": True,
    }


class TelegramPoller:
    def __init__(self, token: str, router: CommandRouter):
        self.token = token
        self.router = router
        self.offset = 0
        self.username = ""

    def api(self, method: str, payload: dict | None = None, timeout: int = 40) -> dict:
        url = f"https://api.telegram.org/bot{self.token}/{method}"
        data = json.dumps(payload or {}).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"{method} HTTP {exc.code}: {detail}") from exc
        if not body.get("ok"):
            raise RuntimeError(f"{method} failed: {body}")
        return body

    def send_photo(self, chat_id: int, photo: bytes, caption: str) -> None:
        boundary = "----SugarBoundary"
        markup = json.dumps(reply_markup())
        chunks = [
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"chat_id\"\r\n\r\n{chat_id}\r\n".encode(),
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"caption\"\r\n\r\n{caption[:1000]}\r\n".encode(),
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"reply_markup\"\r\n\r\n{markup}\r\n".encode(),
            (
                f"--{boundary}\r\nContent-Disposition: form-data; name=\"photo\"; filename=\"the.png\"\r\n"
                "Content-Type: image/png\r\n\r\n"
            ).encode()
            + photo
            + f"\r\n--{boundary}--\r\n".encode(),
        ]
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{self.token}/sendPhoto",
            data=b"".join(chunks),
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        if not body.get("ok"):
            raise RuntimeError(body)

    def set_menu(self) -> None:
        me = self.api("getMe")["result"]
        self.username = me.get("username") or ""
        self.api("setMyCommands", {"commands": [{"command": name, "description": desc} for name, desc in MENU]})
        print(f"Sugar online as @{self.username}. Im nếu không có lệnh / hoặc nút.")

    def deliver(self, chat_id: int, out: Out) -> None:
        self.api("sendChatAction", {"chat_id": chat_id, "action": "upload_photo" if out.photo else "typing"}, timeout=15)
        if out.poll:
            self.api(
                "sendPoll",
                {
                    "chat_id": chat_id,
                    "question": out.poll["question"],
                    "options": [{"text": item} for item in out.poll["options"]],
                    "type": "quiz",
                    "correct_option_id": out.poll["correct"],
                    "open_period": 30,
                    "is_anonymous": True,
                    "reply_markup": reply_markup(),
                },
                timeout=20,
            )
            return
        if out.photo:
            self.send_photo(chat_id, out.photo, out.text)
            return
        self.api(
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": out.text[:4000],
                "disable_web_page_preview": True,
                "reply_markup": reply_markup(),
            },
            timeout=20,
        )

    def handle(self, update: dict) -> None:
        message = update.get("message")
        if not message:
            return
        text = message.get("text") or ""
        chat_id = (message.get("chat") or {}).get("id")
        if chat_id is None:
            return
        sent = message.get("date")
        lag = max(0, int(time.time()) - sent) * 1000 if isinstance(sent, int) else None
        out = self.router.reply(text, {"bot_username": self.username, "lag_ms": lag})
        if out:
            self.deliver(chat_id, out)

    def run(self) -> None:
        self.set_menu()
        while True:
            try:
                body = self.api(
                    "getUpdates",
                    {"offset": self.offset, "timeout": 30, "allowed_updates": ["message"]},
                    timeout=40,
                )
            except RuntimeError as exc:
                text = str(exc)
                if "HTTP 401" in text:
                    print("Token sai. Lấy lại ở @BotFather.", file=sys.stderr)
                    raise SystemExit(1)
                if "HTTP 409" in text:
                    print("Một tiến trình khác đang giữ getUpdates. Tắt nó rồi chạy lại.", file=sys.stderr)
                    raise SystemExit(1)
                print(f"lỗi poll: {exc}", file=sys.stderr)
                time.sleep(2)
                continue
            for update in body.get("result", []):
                self.offset = update["update_id"] + 1
                try:
                    self.handle(update)
                except Exception as exc:  # noqa: BLE001
                    print(f"update lỗi: {exc}", file=sys.stderr)


def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        print("Thiếu TELEGRAM_BOT_TOKEN.", file=sys.stderr)
        raise SystemExit(1)
    TelegramPoller(token, CommandRouter()).run()


if __name__ == "__main__":
    main()
