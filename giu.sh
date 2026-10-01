#!/bin/sh
# Giữ tiến trình sống lại nếu mạng rớt. Không biến máy tắt thành máy chủ.
cd "$(dirname "$0")/.." || exit 1
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
  echo "Thiếu TELEGRAM_BOT_TOKEN" >&2
  exit 1
fi
while true; do
  python3 scripts/bot.py
  echo "Bot thoát, mở lại sau 5 giây" >&2
  sleep 5
done
