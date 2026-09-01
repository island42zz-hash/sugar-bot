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
| `/meme` | `/meme` | Meme crypto ngẫu nhiên (ảnh) |
| `/joke` | `/joke` | Joke crypto/kinh doanh |
| `/fact` | `/fact` | Fact ngẫu nhiên |
| `/8ball <câu hỏi>` | `/8ball nên mua BTC không?` | Quả cầu tiên tri |
| `/roll <NdM>` | `/roll 2d6` | Tung xúc xắc |
| `/flip` | `/flip` | Tung xu Pump/Dump |
| `/truth` / `/dare` | `/truth` | Truth or Dare (crypto/kinh doanh) |
| `/quiz` | `/quiz` | Trivia crypto, poll tự chấm điểm 30s |
| `/confess <text>` | `/confess ...` | Gửi ẩn danh vào group (cần set biến `GROUP_CHAT_ID`) |
| `/top10` | `/top10` | Top 10 crypto theo vốn hóa |
| `/fng` | `/fng` | Chỉ số Sợ hãi & Tham lam (Fear & Greed Index) |
| `/convert <số> <từ> <sang>` | `/convert 100 USD VND` | Quy đổi tiền tệ/crypto (hỗ trợ cả fiat lẫn coin) |
| `/ping` | `/ping` | Đo tốc độ phản hồi bot |
| `/rules` | `/rules` | Xem nội quy group |

`/start` giờ hiện **menu nút bấm** (Công cụ / Thị trường / Vui-Giao lưu / Nội quy)
thay vì list text dài — người mới vào chỉ cần bấm nút, không cần nhớ lệnh.
Bot cũng **tự chào thành viên mới** khi có ai join group.

Tất cả API đều **free, không cần key** — đúng theo pattern hay dùng.
Nội dung joke/fact/8ball/truth/dare/quiz nằm hết trong `fun_content.py`,
sửa thoải mái không cần đụng `bot.py`.

### Kích hoạt /confess (tùy chọn)
1. Thêm bot vào group, lấy `chat_id` của group (cách nhanh: add bot @RawDataBot vào group, nó tự in ra chat_id).
2. Trên Railway → Variables → thêm `GROUP_CHAT_ID` = id đó (thường là số âm, vd `-1001234567890`).
3. Bot phải có quyền gửi tin trong group đó.
