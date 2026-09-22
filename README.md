# 🤖 Sugar Bot

Bot Telegram: tool commands (weather, crypto, translate, calc, short link) +
mảng vui/giao lưu (meme ảnh thật, joke, quiz, truth or dare, câu thâm thúy,
roast) + auto-reply theo keyword trong group. Full tiếng Việt, vibe crypto/kinh doanh.

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
git commit -m "sugar bot"
git branch -M main
git remote add origin https://github.com/<user>/<repo>.git
git push -u origin main
```

## 3. Setup Railway

1. Railway → New Project → Deploy from GitHub repo → chọn repo này.
2. Đặt tên service khớp với `--service` trong `.github/workflows/deploy.yml`
   (mặc định là `worker`, theo tên trong `Procfile`).
3. Variables → thêm `BOT_TOKEN` = token từ @BotFather.

## 4. GitHub Actions auto-deploy

1. Repo → Settings → Secrets and variables → Actions → New repository secret
2. `RAILWAY_TOKEN` = token lấy từ railway.app/account/tokens

Từ giờ mỗi lần push vào `main`, bot tự deploy lại.

## 5. Sửa nội dung

- `triggers.json` — cặp từ khóa / câu auto-reply
- `fun_content.py` — joke, fact, 8ball, truth, dare, quiz, câu thâm thúy, roast

## Commands

| Lệnh | Mô tả |
|---|---|
| `/weather <city>` | Thời tiết hiện tại |
| `/crypto <coin>` | Giá + biến động 24h (Binance, fallback CoinGecko) |
| `/translate <text>` | Dịch nhanh |
| `/calc <expr>` | Máy tính |
| `/short <url>` | Rút gọn link |
| `/convert <số> <từ> <sang>` | Quy đổi tiền tệ/crypto |
| `/ping` | Đo tốc độ phản hồi |
| `/top10` | Top 10 coin theo vốn hóa |
| `/fng` | Chỉ số Sợ hãi & Tham lam |
| `/stocks` | Chứng khoán thế giới — S&P500, Dow Jones, Nasdaq, Nikkei, Hang Seng, FTSE, DAX |
| `/news [vn\|kinhdoanh\|crypto]` | Tin tức Việt Nam (VnExpress, Coin68) |
| `/meme` | **Ảnh meme thật**, ngẫu nhiên |
| `/joke` | Joke crypto/kinh doanh |
| `/fact` | Fact thú vị |
| `/8ball <câu hỏi>` | Quả cầu tiên tri |
| `/roll <NdM>` | Tung xúc xắc |
| `/flip` | Tung xu Pump/Dump |
| `/truth`, `/dare` | Truth or Dare |
| `/thamthuy` | Câu nói thâm thúy |
| `/roast` | Troll nhẹ thị trường (không nhắm ai cụ thể) |
| `/quiz` | Trivia crypto, poll 30s |
| `/confess <text>` | Confession ẩn danh (cần `GROUP_CHAT_ID`) |
| `/rules` | Nội quy group |

`/start` hiện menu nút bấm, bot tự chào thành viên mới khi có ai join group
(cần tắt Group Privacy Mode qua @BotFather).

**Auto-reply chỉ kích hoạt khi trúng từ khóa trong `triggers.json`** — không
trả lời mọi tin nhắn để tránh spam chat.

## Tính năng "sống động" mới

- **Reaction ngẫu nhiên**: ~10% tin nhắn trong group, bot tự thả emoji (🔥😂👀🚀...)
  vào tin nhắn — không kèm text, chỉ react cho vui.
- **Buông câu troll khi im ắng**: sau khoảng 15-30 tin nhắn không ai trigger bot,
  nó tự nhắn 1 câu trong `IDLE_CHATTER` (sửa trong `fun_content.py`).
- **Bản tin tự động 3 lần/ngày** (giờ VN, cần `GROUP_CHAT_ID`):
  - **8:00 sáng** — giá BTC, Fear & Greed, 1 tin kinh doanh, fact + joke
  - **12:30 trưa** — giá BTC, 1 tin crypto (Coin68), quả cầu tiên tri
  - **20:00 tối** — giá BTC, Fear & Greed, 1 tin tổng hợp, câu thâm thúy
  - Nếu chưa set `GROUP_CHAT_ID` thì bản tin không chạy, mọi lệnh khác vẫn bình thường.
- **`/news [vn|kinhdoanh|crypto]`** — xem tin bất cứ lúc nào, không cần đợi giờ tự động.
  - `vn` — VnExpress tin mới nhất
  - `kinhdoanh` — VnExpress mục Kinh doanh
  - `crypto` — Coin68 (tin crypto tiếng Việt)

### Cách lấy GROUP_CHAT_ID
1. Add bot **@RawDataBot** vào group (tạm thời)
2. Nó tự nhắn JSON, tìm dòng `"chat":{"id": -100xxxxxxxxxx}` — copy số đó (kèm dấu `-`)
3. Xóa @RawDataBot ra khỏi group
4. Railway → service worker → Variables → thêm `GROUP_CHAT_ID` = số vừa copy

## Ghi chú về GRAM

"Gram" là tên gốc dự án tiền số của Telegram (2018), bị hủy năm 2020 do vướng
SEC Mỹ. Cộng đồng sau đó lập lại thành **TON (The Open Network)** — coin thật
đang giao dịch. Gõ `/crypto GRAM` bot sẽ tự hiểu và trả về giá TON kèm ghi chú.

## Logo coin

`/crypto <coin>` giờ gửi kèm ảnh logo thật của coin (lấy từ CoinGecko) thay vì
chỉ text — nếu không lấy được logo, bot tự động rơi về text thuần, không lỗi.

Tất cả API đều free, không cần key.
