# Commands and sources

## Buttons

Công cụ, Thị trường, Vui / Giao lưu, Nội quy. These are reply-keyboard labels, not slash commands. A matching text message opens that list.

## Sources

| Command | Source | On failure |
|---|---|---|
| /gia /xephang | CoinGecko public | `source_fail` or "không thấy mã" |
| /anhche /meme | meme-api.com, bỏ ảnh nhạy cảm. Hết nguồn thì thẻ chữ | thẻ chữ dự phòng |
| /socamxuc | alternative.me fear-and-greed | `source_fail` |
| /chungkhoan | Stooq CSV | per-index "chưa lấy được" |
| /tintuc | VnExpress RSS | `source_fail` |
| /thoittiet | Open-Meteo | `source_fail` or city miss |
| /dich | MyMemory | `source_fail` |
| /rutgon | is.gd | `source_fail` |
| /doitien | Frankfurter | Vietnamese pair error |

Do not scrape a page to fill a price.

## Images

`cards.welcome_card`, `price_card`, `mood_card`, `meme_card`, `list_card` return PNG bytes. Poller sends them with `sendPhoto` and the persistent keyboard.

## Railway

Rainway streams a home screen. It does not host this process. Railway does.

Deploy this folder as one worker. Start command: `python scripts/bot.py`. Set `TELEGRAM_BOT_TOKEN` in the service variables. Do not add a public domain. One replica only. The bot stays up while that service is running and the account can pay the usage.



## Webhook

Stay on long polling unless the user gives public HTTPS. Stop polling before `setWebhook`.

## Errors

| API | Action |
|---|---|
| 401 | Stop. Ask for a new BotFather token |
| 409 | Stop the other poller |
| 429 | Wait `retry_after` |
| empty long poll | Call getUpdates again |
