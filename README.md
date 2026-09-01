# 🤖 Sugar Bot

Bot Telegram: tool commands (weather, crypto, translate, calc, short link) + auto-reply theo keyword trong group.

## 1. Chạy thử local

```bash
pip install -r requirements.txt
export BOT_TOKEN="token_tu_botfather"
python bot.py
```

## 2. Push lên GitHub

```bash
git init
git add .
git commit -m "sugar bot v1"
git branch -M main
git remote add origin https://github.com/<user>/<repo>.git
git push -u origin main
```

## 3. Setup Railway (chỉ cần làm 1 lần)

1. Vào https://railway.app → New Project → tạo project (đặt tên service là `sugar-bot`,
   nếu đặt tên khác thì sửa lại `--service sugar-bot` trong
   `.github/workflows/deploy.yml`).
2. Vào tab **Variables** của service → thêm biến:
   - `BOT_TOKEN` = token bot lấy từ @BotFather
3. Lấy Railway API token: https://railway.app/account/tokens → tạo token mới.

## 4. Setup GitHub Actions auto-deploy

1. Vào repo GitHub → **Settings → Secrets and variables → Actions**
2. Thêm secret mới: `RAILWAY_TOKEN` = token lấy ở bước 3.
3. Xong! Từ giờ mỗi lần `git push` vào nhánh `main`, GitHub Actions sẽ tự chạy
   `railway up` và deploy bản mới lên Railway.

## 5. Sửa auto-reply

Mở `triggers.json`, thêm/sửa cặp `"keyword": "câu trả lời"`. Không cần sửa code,
chỉ cần commit + push là bot tự cập nhật sau khi deploy lại.

## Commands

| Lệnh | Ví dụ | Mô tả |
|---|---|---|
| `/weather <city>` | `/weather Phu Quoc` | Thời tiết hiện tại (Open-Meteo, free) |
| `/crypto <coin>` | `/crypto BTC` | Giá + biến động 24h (CoinGecko, free) |
| `/translate <text>` | `/translate xin chao` | Dịch nhanh (auto-detect → vi) |
| `/translate <lang> <text>` | `/translate en xin chao` | Dịch sang ngôn ngữ chỉ định |
| `/calc <expr>` | `/calc (12+8)*3/2` | Máy tính (+ - * / // % **) |
| `/short <url>` | `/short https://...` | Rút gọn link (is.gd, free) |

Tất cả API đều **free, không cần key** — đúng theo pattern hay dùng.
