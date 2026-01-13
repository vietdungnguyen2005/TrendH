# Hướng dẫn tạo Reddit App để lấy API Credentials

## 📋 Bước 1: Đăng nhập Reddit

1. Truy cập: https://www.reddit.com
2. Đăng nhập tài khoản Reddit của bạn (hoặc tạo tài khoản mới nếu chưa có)

---

## 🔧 Bước 2: Tạo Reddit App

### 2.1 Truy cập trang Apps
- Vào: https://www.reddit.com/prefs/apps
- Hoặc: Reddit Settings → Safety & Privacy → Apps

### 2.2 Tạo App mới
1. Cuộn xuống dưới cùng
2. Click nút **"Create App"** hoặc **"Create Another App"**

### 2.3 Điền thông tin App

```
Name: TrendHunter
App type: ○ web app  ○ installed app  ● script
Description: Trend Hunter - Product trend analysis tool
About URL: (để trống)
Redirect URI: http://localhost:8080
```

**Quan trọng:** Chọn **"script"** làm app type!

### 2.4 Click "Create app"

---

## 🔑 Bước 3: Lấy Credentials

Sau khi tạo xong, bạn sẽ thấy thông tin app như sau:

```
TrendHunter
──────────────────────────────
personal use script

[LONG STRING OF CHARACTERS]  ← Đây là CLIENT_ID
──────────────────────────────
secret: [ANOTHER LONG STRING] ← Đây là CLIENT_SECRET
```

### Ví dụ cụ thể:

```
CLIENT_ID:     abcDEF123xyz  (dưới chữ "personal use script")
CLIENT_SECRET: XyZ789-AbC123-DeF456_GhI  (sau chữ "secret:")
```

---

## 💾 Bước 4: Cấu hình trong Trend Hunter

### 4.1 Tạo file .env

Trong thư mục `d:\TrendHunter\`, tạo file `.env`:

```powershell
# Trong PowerShell
cd d:\TrendHunter
copy .env.example .env
notepad .env
```

### 4.2 Điền credentials vào .env

Mở file `.env` và điền thông tin:

```env
# Reddit API credentials
REDDIT_CLIENT_ID=abcDEF123xyz
REDDIT_CLIENT_SECRET=XyZ789-AbC123-DeF456_GhI
REDDIT_USER_AGENT=TrendHunter/0.1

# Telegram Bot (optional - để sau)
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Email (optional - để sau)
EMAIL_SENDER=
EMAIL_PASSWORD=
EMAIL_RECIPIENTS=
```

**Lưu ý:** 
- Thay `abcDEF123xyz` bằng CLIENT_ID thực của bạn
- Thay `XyZ789-AbC123-DeF456_GhI` bằng CLIENT_SECRET thực của bạn
- **KHÔNG** có dấu ngoặc kép hoặc khoảng trắng thừa

---

## ✅ Bước 5: Kiểm tra

Chạy lệnh sau để test kết nối Reddit:

```powershell
python -c "from crawler.reddit import RedditCrawler; print('Testing...'); c = RedditCrawler(); print('✅ Reddit API connected successfully!')"
```

### Nếu gặp lỗi:

#### Lỗi 1: "Reddit API credentials not configured"
→ File `.env` chưa được tạo hoặc chưa có thông tin

#### Lỗi 2: "401 Unauthorized" 
→ CLIENT_ID hoặc CLIENT_SECRET sai, kiểm tra lại

#### Lỗi 3: "403 Forbidden"
→ App type phải là "script", không phải "web app"

---

## 🚀 Bước 6: Chạy Crawler

Sau khi cấu hình xong:

```powershell
# Chạy crawler đầy đủ
python run_crawler.py

# Hoặc chỉ test Reddit
python -c "from crawler.reddit import RedditCrawler; c = RedditCrawler(); result = c.run(); print(result)"
```

---

## 📸 Hình minh họa

### Giao diện tạo Reddit App:

```
┌─────────────────────────────────────────────┐
│  Create Application                         │
├─────────────────────────────────────────────┤
│  Name: TrendHunter                          │
│                                             │
│  App type:                                  │
│  ○ web app                                  │
│  ○ installed app                            │
│  ● script  ← CHỌN CÁI NÀY                   │
│                                             │
│  Description: Trend Hunter tool             │
│                                             │
│  About URL: (không bắt buộc)                │
│                                             │
│  Redirect URI: http://localhost:8080        │
│                                             │
│            [ Create app ]                   │
└─────────────────────────────────────────────┘
```

### Sau khi tạo xong:

```
┌─────────────────────────────────────────────┐
│  TrendHunter                      [Edit]    │
├─────────────────────────────────────────────┤
│  personal use script                        │
│                                             │
│  abcDEF123xyz  ← CLIENT_ID                  │
│                                             │
│  secret: XyZ789-AbC123  ← CLIENT_SECRET     │
│                                             │
│  description: Trend Hunter tool             │
│                                             │
│            [ Delete ] [ Edit ]              │
└─────────────────────────────────────────────┘
```

---

## ⚠️ Lưu ý quan trọng

1. **Bảo mật:** KHÔNG share CLIENT_SECRET với ai
2. **Git:** File `.env` đã được thêm vào `.gitignore` - KHÔNG commit lên GitHub
3. **Rate Limits:** Reddit giới hạn 60 requests/phút cho script apps
4. **User Agent:** Phải có format đúng (đã config sẵn trong code)

---

## 🔗 Tài liệu tham khảo

- Reddit API Documentation: https://www.reddit.com/dev/api
- PRAW (Python Reddit API Wrapper): https://praw.readthedocs.io/
- Reddit Apps Manager: https://www.reddit.com/prefs/apps

---

## 🆘 Troubleshooting

### Không tìm thấy nút "Create App"?
→ Đảm bảo đã đăng nhập Reddit và email đã được xác thực

### App bị từ chối?
→ Kiểm tra tên app không chứa ký tự đặc biệt

### Crawler không lấy được data?
→ Kiểm tra subreddits trong `config/config.yaml` có tồn tại không

### Rate limit exceeded?
→ Giảm `fetch_limit` trong config hoặc tăng delay giữa các requests

---

## ✨ Sau khi setup xong

Bạn có thể:
1. Chạy crawler định kỳ với scheduler
2. Thu thập data từ 5 subreddits đã config
3. Tiếp tục triển khai Milestone 2 (Filtering & Entity Extraction)

**Good luck! 🚀**
