# Trend Hunter - Hướng dẫn Setup

## 🚀 Bước 1: Clone Repository & Setup

```powershell
# Di chuyển vào thư mục dự án
cd d:\TrendHunter

# Tạo virtual environment
python -m venv venv

# Kích hoạt virtual environment
.\venv\Scripts\activate

# Cài đặt dependencies
pip install -r requirements.txt

# Cài đặt Playwright browsers (cho TikTok crawler)
playwright install chromium
```

## 🗄️ Bước 2: Khởi tạo Database

```powershell
# Chạy script khởi tạo database
python init_db.py
```

Kết quả mong đợi:
- Tạo file `data/trendhunter.db`
- Tạo 8 tables: sources_raw, keywords, time_series_metrics, features, flags, ground_truth, jobs_log, cache
- Hiển thị thông báo "✅ Database initialization completed successfully!"

## ⚙️ Bước 3: Cấu hình

### 3.1 Tạo file .env

```powershell
# Copy file mẫu
copy .env.example .env

# Sửa file .env với editor
notepad .env
```

### 3.2 Cấu hình Reddit API (Bắt buộc cho Milestone 1)

1. Truy cập: https://www.reddit.com/prefs/apps
2. Tạo app mới (script type)
3. Copy `client_id` và `client_secret`
4. Paste vào file `.env`:

```
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
```

### 3.3 Cấu hình Telegram (Optional - cho alerts)

1. Tạo bot với @BotFather trên Telegram
2. Lấy bot token
3. Gửi message cho bot và lấy chat_id từ: https://api.telegram.org/bot<TOKEN>/getUpdates
4. Thêm vào `.env`

## ✅ Bước 4: Kiểm tra Setup

```powershell
# Test import các module
python -c "from utils.config_loader import get_config; from utils.db_utils import get_db; print('✅ Setup OK!')"

# Kiểm tra database
python -c "from utils.db_utils import get_db; db = get_db(); print('Tables:', db.execute_query('SELECT name FROM sqlite_master WHERE type=\"table\"'))"
```

## 📁 Cấu trúc thư mục

```
TrendHunter/
├── config/              # Configuration files
│   ├── config.yaml      # Main config
│   └── blacklist.yaml   # Spam/filter lists
├── crawler/             # Data collection modules
├── processing/          # Filtering & extraction
├── verification/        # Google Trends wrapper
├── features/            # Feature engineering
├── scoring/             # Scoring engine
├── backtest/            # Backtest framework
├── ui/                  # Streamlit dashboard
├── utils/               # Utility modules
├── data/                # Database & data files
├── logs/                # Log files
├── init_db.py          # Database initialization
├── scheduler.py        # Job scheduler
├── requirements.txt    # Python dependencies
├── .env                # Environment variables (git-ignored)
└── README.md           # Project documentation
```

## 🔜 Tiếp theo

Sau khi setup xong, bắt đầu **Milestone 1 - MVP Crawler**:
- Xây dựng Reddit Crawler
- Xây dựng TikTok Crawler
- Test thu thập dữ liệu

## 📝 Ghi chú

- Python version: >= 3.9
- RAM tối thiểu: 8GB
- Disk space: ~5GB (cho database & logs)
- Internet: Cần kết nối ổn định cho crawling

## ⚠️ Lưu ý

1. **KHÔNG** commit file `.env` vào git (đã có trong .gitignore)
2. Tuân thủ rate limits của các nền tảng
3. Đọc Terms of Service của Reddit, TikTok trước khi crawl
4. Backup database định kỳ

## 🆘 Troubleshooting

### Lỗi: "ModuleNotFoundError"
```powershell
# Đảm bảo venv đã được activate
.\venv\Scripts\activate
# Cài lại dependencies
pip install -r requirements.txt
```

### Lỗi: "playwright: command not found"
```powershell
# Cài đặt browsers
playwright install
```

### Lỗi database locked
```powershell
# Đóng tất cả connections đến DB
# Hoặc xóa file .db-journal nếu có
```
