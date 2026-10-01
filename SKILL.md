---
name: trend-telegram-bot
description: "Build Sugar, a Vietnamese Telegram group bot that answers slash commands and category buttons with image cards. Use when upgrading a Telegram bot, adding /commands, market cards, or making bot copy fully Vietnamese."
type: tool
lifecycle: active
---

# Sugar Super Bot — thuần Việt, có thẻ ảnh

Ship a group bot that stays silent on normal chat, answers `/commands` and the four category buttons, and sends a PNG card for welcome, price, rank, mood, and meme.

## When to use

Use for Sugar or a similar Vietnamese community bot. Do not use for Discord, or for a bot that should answer every sentence.

## Decide first

| Choice | Default | Switch when |
|---|---|---|
| Language | Vietnamese in every user-visible string | User asks for bilingual → add a second copy file, do not mix English into the menu |
| Commands | Vietnamese slugs in `MENU` | Old English commands stay as hidden `ALIASES` only |
| Images | `scripts/cards.py` draws the card | User supplies a logo → pass it into the card header |
| Data | Public HTTP, failure in Vietnamese | No network → return the offline sentence, never invent a price |

## Build workflow

1. Read `assets/copy.json` before writing a line the user will see.
2. Add a command on `CommandRouter`, then add it to `MENU` and the right group in `GROUPS`.
3. If the reply is a number, rank, or joke image, return `Out(text, photo=cards....)`.
4. Do not put file paths, variable names, or "edit this in code" into chat text.
5. Market replies end with `COPY["market_note"]`.
6. Run `python3 scripts/selftest.py`. Then start with `TELEGRAM_BOT_TOKEN`.

```bash
export TELEGRAM_BOT_TOKEN="123456:ABC..."
python3 scripts/bot.py
```

## Reply rules

- Ignore plain text. Answer `/command` and the four button labels only.
- In groups, ignore `/lenh@botkhac`.
- Public menu is Vietnamese. English aliases may route, but must not appear in `/trogiup`.
- Price, rank, mood, and meme go out as a photo plus a short caption.
- Confession is not a reply to the sender. Still say it is hidden from the group, not from the bot.
- Never invent a live price. On HTTP failure, send `COPY["source_fail"]`.

## Files

| Path | Load when |
|---|---|
| `scripts/bot.py` | Running or adding a command |
| `scripts/cards.py` | Changing the card layout |
| `assets/copy.json` | Any user-facing sentence |
| `assets/fun.json` | Jokes, quizzes, truths |
| `references/commands.md` | Transport, sources, errors |
| `references/persona.md` | Voice and what not to say |

## Common issues

| Symptom | Fix |
|---|---|
| Menu still English | Command was added only as an alias. Put the Vietnamese slug in `MENU` |
| Dev note in chat | Delete it from `copy.json`. Rules come from that file only |
| Photo missing | Handler returned a string. Return `Out(..., photo=...)` |
| 409 on start | Another poller holds `getUpdates`. Stop it |
| Price blank | CoinGecko miss. Say the symbol was not found. Do not fill a number |
