#!/usr/bin/env python3
"""Kiểm tra router Sugar, không cần mạng."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bot import CommandRouter, extract_command  # noqa: E402


def main() -> None:
    router = CommandRouter(online=False)
    checks = []

    def check(name: str, ok: bool) -> None:
        checks.append((name, ok))
        print(("ok  " if ok else "FAIL") + " " + name)

    check("im tin thuong", router.reply("hi bro") is None)
    start = router.reply("/batdau")
    check("chao co anh", start is not None and start.photo is not None and "sẵn sàng" in start.text)
    help_text = router.reply("Công cụ").text
    check("cong cu thuan viet", "/thoittiet" in help_text and "weather" not in help_text.lower())
    market = router.reply("Thị trường").text
    check("thi truong viet", "/gia" in market and "/crypto" not in market)
    rules = router.reply("/noiquy").text
    check("noiquy khong lo dev", "fun_content" not in rules and "Nội quy" in rules)
    meme = router.reply("/anhche")
    check("anh che co the", meme.photo is not None and meme.photo[:8] == b"\x89PNG\r\n\x1a\n")
    check("alias cu van chay", router.reply("/help") is not None)
    check("bot khac bi bo", router.reply("/trogiup@khac", {"bot_username": "sugar_bot"}) is None)
    check("tinh", "20" in router.reply("/tinh (12+8)*1").text)
    check("tinh chan", "không làm" in router.reply("/tinh __import__('os')").text)
    check("xuc xac", "Tổng" in router.reply("/xucxac 2d6").text)
    quiz = router.reply("/dovui")
    check("do vui la poll", quiz.poll is not None and quiz.poll["open_period"] == 30)
    confess = router.reply("/tamtinh hôm nay chốt non")
    check("tam tinh an", confess.anonymous and "chốt non" in confess.text)
    check("lenh la", extract_command("/Gia@Sugar_Bot btc", "sugar_bot") == ("gia", "btc"))
    menu = router.reply("/trogiup").text
    check("help khong tieng anh lenh", "ping" not in menu and "meme" not in menu)

    failed = [name for name, ok in checks if not ok]
    if failed:
        raise SystemExit(f"{len(failed)} failed: {', '.join(failed)}")
    print(f"{len(checks)} checks passed")


if __name__ == "__main__":
    main()
