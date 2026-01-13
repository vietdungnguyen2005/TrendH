# 📋 DANH SÁCH CÔNG VIỆC CHI TIẾT - TREND HUNTER

> Tài liệu này liệt kê tất cả các công việc cần làm theo từng Milestone của dự án Trend Hunter.

---

## 🟢 MILESTONE 0 — Chuẩn bị môi trường (Day 0)

| # | Công việc | Mô tả chi tiết | Trạng thái |
|---|-----------|----------------|------------|
| 0.1 | Khởi tạo Git repository | Tạo repo, thiết lập .gitignore, cấu trúc thư mục chuẩn | ✅ |
| 0.2 | Thiết lập virtual environment | Tạo venv Python, requirements.txt với các thư viện cốt lõi | ✅ |
| 0.3 | Cài đặt dependencies cơ bản | praw, playwright, pytrends, pandas, streamlit, sqlite3 | ✅ |
| 0.4 | Tạo SQLite database schema | Script init_db.py tạo các bảng: sources_raw, keywords, time_series_metrics, features, flags | ✅ |
| 0.5 | Cấu hình scheduler template | Tạo cron/task scheduler template cho chạy batch | ✅ |
| 0.6 | Tạo file config mẫu | config.yaml/json cho API keys, subreddit list, thresholds | ✅ |
| 0.7 | Kiểm thử khởi tạo DB | Chạy script init, verify tables được tạo đúng | ✅ |

**Tiêu chí hoàn thành:** Sẵn sàng chạy crawler mock ✅

---

## 🟡 MILESTONE 1 — MVP Crawler + Storage (Week 1)

| # | Công việc | Mô tả chi tiết | Trạng thái |
|---|-----------|----------------|------------|
| 1.1 | Xây dựng Reddit Crawler | crawler/reddit.py sử dụng PRAW hoặc JSON API | ✅ |
| 1.2 | Cấu hình danh sách 5 subreddits | Chọn subreddits phù hợp với niche, thêm vào config | ✅ |
| 1.3 | Xây dựng TikTok Crawler | crawler/tiktok.py scrape TikTok Creative Center | ✅ |
| 1.4 | Thiết lập Playwright automation | Cài đặt browser, xử lý dynamic content | ✅ |
| 1.5 | Tạo data models/schema | Định nghĩa class cho sources_raw record | ✅ |
| 1.6 | Viết hàm lưu vào DB | Insert batch vào sources_raw table | ✅ |
| 1.7 | Tạo scheduler script | run_crawler.py với logging, error handling | ✅ |
| 1.8 | Cấu hình cron job | Thiết lập chạy hourly | ✅ |
| 1.9 | Kiểm thử crawl rate | Verify ≥100 items/run | ✅ |
| 1.10 | Kiểm thử failed rate | Đảm bảo <5% failed requests | ✅ |
| 1.11 | Chạy thử 48h liên tục | Monitor & fix bugs | 🔄 |

**Tiêu chí hoàn thành:** Có dữ liệu thô liên tục 48 giờ (Đã sẵn sàng - cần config Reddit API)

---

## 🟠 MILESTONE 2 — Filtering & Entity Extraction (Week 1-2)

| # | Công việc | Mô tả chi tiết | Trạng thái |
|---|-----------|----------------|------------|
| 2.1 | Xây dựng Blacklist | Danh sách từ khóa spam, quảng cáo, chính trị | ⬜ |
| 2.2 | Viết filtering.py | Rule-based filter: spam detection, ads removal | ⬜ |
| 2.3 | Tạo regex patterns | Pattern nhận diện promo codes, affiliate links | ⬜ |
| 2.4 | Xây dựng Entity Extractor | entity_extraction.py: NLP basic (n-grams, NER) | ⬜ |
| 2.5 | Cài đặt spaCy/NLTK | Lightweight NLP toolkit | ⬜ |
| 2.6 | Viết Variant Normalizer | Chuẩn hóa: lowercase, remove special chars, stemming | ⬜ |
| 2.7 | Xây dựng Canonical Mapping | Nhóm variants về canonical term (VD: "airpod" → "airpods") | ⬜ |
| 2.8 | Tạo keywords table population | Insert canonical terms + variants_json | ⬜ |
| 2.9 | Sample audit 500 items | Đánh giá false_drop_rate ≤10% | ⬜ |
| 2.10 | Verify variant grouping | Đảm bảo purity ≥85% | ⬜ |
| 2.11 | Kiểm tra daily keywords count | Target ≥1k canonical keywords/ngày | ⬜ |

**Tiêu chí hoàn thành:** Danh sách canonical keywords mỗi ngày ≥1k

---

## 🔵 MILESTONE 3 — Pytrends Wrapper & Verification (Week 2)

| # | Công việc | Mô tả chi tiết | Trạng thái |
|---|-----------|----------------|------------|
| 3.1 | Viết pytrends_wrapper.py | Wrapper class cho pytrends API | ⬜ |
| 3.2 | Implement Replicate Sampling | Gọi n=3 lần, tính median | ⬜ |
| 3.3 | Xây dựng Cache Layer | SQLite hoặc Redis cache, TTL 24h | ⬜ |
| 3.4 | Batch Query Handler | Gom terms thành batches (5 terms/request) | ⬜ |
| 3.5 | Rate Limiter | Delay between requests, backoff strategy | ⬜ |
| 3.6 | Error Handler cho 429 | Catch & retry với exponential backoff | ⬜ |
| 3.7 | Lưu raw samples | Persist raw_samples_json vào time_series_metrics | ⬜ |
| 3.8 | Tính median IOT series | Aggregation function cho replicate data | ⬜ |
| 3.9 | Kiểm thử 100 terms | Verify successful_rate ≥95% | ⬜ |
| 3.10 | Kiểm tra cache hit rate | Target >60% cache hits | ⬜ |
| 3.11 | Tạo test suite | Unit tests cho wrapper | ⬜ |

**Tiêu chí hoàn thành:** Median IOT series cho mỗi term có sẵn

---

## 🟣 MILESTONE 4 — Feature Engineering & Scoring Rules (Week 2-3)

| # | Công việc | Mô tả chi tiết | Trạng thái |
|---|-----------|----------------|------------|
| 4.1 | Viết feature_engineering.py | Pipeline tính features từ raw data | ⬜ |
| 4.2 | Tính Slope | Linear regression slope trên IOT series | ⬜ |
| 4.3 | Tính Acceleration | Second derivative, rate of change của slope | ⬜ |
| 4.4 | Tính Moving Averages | MA3, MA7 cho IOT series | ⬜ |
| 4.5 | Tính pct_change_24h | Percentage change so với 24h trước | ⬜ |
| 4.6 | Tính platform_count | Số platforms term xuất hiện (Reddit, TikTok) | ⬜ |
| 4.7 | Tính novelty_score | Inverse of term age / frequency | ⬜ |
| 4.8 | Tính influencer_weighted | Mentions weighted by author influence | ⬜ |
| 4.9 | Thiết kế Scoring Formula | Weight config: w1*slope + w2*accel + ... | ⬜ |
| 4.10 | Viết scoring_engine.py | Rule-based scorer trả TrendScore | ⬜ |
| 4.11 | Định nghĩa Labels | Hidden Gem, Breakout, Stable, Dying | ⬜ |
| 4.12 | Tạo reason_codes | Giải thích tại sao được flag | ⬜ |
| 4.13 | Generate flags table | Populate flags với scores & labels | ⬜ |
| 4.14 | Feature coverage check | Verify ≥95% terms có đủ features | ⬜ |
| 4.15 | Manual sanity check | Review top-100 flags, target 50%+ chất lượng | ⬜ |

**Tiêu chí hoàn thành:** Top-50 flags có 50%+ chất lượng theo kiểm tra manual

---

## 🔴 MILESTONE 5 — Backtest Framework (Week 3-4)

| # | Công việc | Mô tả chi tiết | Trạng thái |
|---|-----------|----------------|------------|
| 5.1 | Định nghĩa Ground-truth | Criteria: IOT tăng 100% HOẶC top TikTok/Reddit | ⬜ |
| 5.2 | Viết labeling script | Auto-label historical data theo ground-truth | ⬜ |
| 5.3 | Viết rolling_cv.py | Rolling-window cross-validation (14d train, 7d test) | ⬜ |
| 5.4 | Implement Precision@K | Tính Precision@50, Precision@100 | ⬜ |
| 5.5 | Implement Recall@7d | Tính recall trong 7-day window | ⬜ |
| 5.6 | Implement Lead Time | Median hours từ flag đến trend peak | ⬜ |
| 5.7 | Implement FPR | False Positive Rate calculation | ⬜ |
| 5.8 | Tạo Backtest Reports | Export HTML/CSV với charts & metrics | ⬜ |
| 5.9 | Threshold Tuning | Grid search tìm optimal thresholds | ⬜ |
| 5.10 | Chạy backtest full data | Test trên ≥2-4 tuần data | ⬜ |
| 5.11 | Quyết định production thresholds | Lock thresholds cho deployment | ⬜ |
| 5.12 | Document backtest results | Lưu artifacts, checkpoints | ⬜ |

**Tiêu chí hoàn thành:** Threshold được quyết định cho production

---

## ⚪ MILESTONE 6 — UI & Alerts (Week 4)

| # | Công việc | Mô tả chi tiết | Trạng thái |
|---|-----------|----------------|------------|
| 6.1 | Xây dựng Streamlit app.py | Main dashboard application | ⬜ |
| 6.2 | Trang Top Flags | Table hiển thị top trending flags | ⬜ |
| 6.3 | IOT Chart component | Line chart cho Google Trends data | ⬜ |
| 6.4 | Mentions Chart | Bar chart Reddit/TikTok mentions | ⬜ |
| 6.5 | Raw Posts Viewer | Hiển thị original posts liên quan | ⬜ |
| 6.6 | Filter & Search | Filter by label, date range, score | ⬜ |
| 6.7 | Export CSV function | Download data dạng CSV | ⬜ |
| 6.8 | Cấu hình Telegram Bot | Tạo bot, lấy chat_id | ⬜ |
| 6.9 | Viết alert_service.py | Send alerts cho high-confidence flags | ⬜ |
| 6.10 | Email Alert (optional) | SMTP integration | ⬜ |
| 6.11 | Alert Config | Thresholds cho alert triggers | ⬜ |
| 6.12 | End-to-end test | Flag → Alert delivered verification | ⬜ |
| 6.13 | User documentation | Hướng dẫn sử dụng dashboard | ⬜ |

**Tiêu chí hoàn thành:** Stakeholder xác nhận dashboard hữu dụng

---

## ⚫ MILESTONE 7 — Hardening & Ops (Week 5)

| # | Công việc | Mô tả chi tiết | Trạng thái |
|---|-----------|----------------|------------|
| 7.1 | Viết ip_reset.py | Script reset IP Dcom 4G | ⬜ |
| 7.2 | Implement Retry Utils | Exponential backoff, max retries | ⬜ |
| 7.3 | Caching optimization | In-memory + disk cache layers | ⬜ |
| 7.4 | Log Rotation | Logrotate config, structured JSON logs | ⬜ |
| 7.5 | DB Backup Script | Daily SQLite dump, weekly snapshots | ⬜ |
| 7.6 | Health Check endpoint | Status API cho monitoring | ⬜ |
| 7.7 | 429 Auto-handler | Auto-suspend & ip_reset trigger | ⬜ |
| 7.8 | Ingestion Alert | Alert khi count < expected | ⬜ |
| 7.9 | Precision Drift Alert | Warn khi giảm >10% so baseline | ⬜ |
| 7.10 | Simulate stress test | Test 429 events, verify auto-throttle | ⬜ |
| 7.11 | Failover procedures | Document & test recovery steps | ⬜ |
| 7.12 | Production deployment | Final deployment checklist | ⬜ |

**Tiêu chí hoàn thành:** System chịu đựng spike requests mà không crash

---

## 🌟 MILESTONE 8 — Optional: ML Re-ranker (Month 2+)

| # | Công việc | Mô tả chi tiết | Trạng thái |
|---|-----------|----------------|------------|
| 8.1 | Thu thập ground-truth labels | ≥1 tháng labeled data | ⬜ |
| 8.2 | Feature Engineering cho ML | Additional features, feature selection | ⬜ |
| 8.3 | Viết train_model.py | LightGBM training pipeline | ⬜ |
| 8.4 | K-Fold Cross Validation | Rolling CV để tránh data leakage | ⬜ |
| 8.5 | Hyperparameter Tuning | Grid/Random search | ⬜ |
| 8.6 | Model Evaluation | Compare vs rule-based baseline | ⬜ |
| 8.7 | Export model artifacts | Save model, scaler, feature list | ⬜ |
| 8.8 | Integration vào scoring | Re-ranker overlay on rule-based | ⬜ |
| 8.9 | A/B Test setup | Production A/B test framework | ⬜ |
| 8.10 | Monitoring ML drift | Track model performance over time | ⬜ |

**Tiêu chí hoàn thành:** Model đưa vào production A/B test

---

## 📊 TỔNG KẾT

| Milestone | Số công việc | Timeline | Tiến độ |
|-----------|--------------|----------|---------|
| M0 - Chuẩn bị | 7 | Day 0 | 7/7 ✅ |
| M1 - Crawler | 11 | Week 1 | 10/11 🔄 |
| M2 - Filtering | 11 | Week 1-2 | 0/11 |
| M3 - Pytrends | 11 | Week 2 | 0/11 |
| M4 - Features | 15 | Week 2-3 | 0/15 |
| M5 - Backtest | 12 | Week 3-4 | 0/12 |
| M6 - UI/Alerts | 13 | Week 4 | 0/13 |
| M7 - Hardening | 12 | Week 5 | 0/12 |
| M8 - ML (Optional) | 10 | Month 2+ | 0/10 |
| **TỔNG** | **102** | **5 tuần + optional** | **17/102** |

---

## 📝 Ghi chú

### Ký hiệu trạng thái:
- ⬜ Chưa bắt đầu
- 🔄 Đang thực hiện
- ✅ Hoàn thành
- ❌ Bỏ qua/Không cần

### Cập nhật gần nhất:
- **Ngày:** 2026-01-14
- **Người cập nhật:** GitHub Copilot
- **Ghi chú:** Hoàn thành Milestone 0 và hầu hết Milestone 1 (Crawlers + Storage)

---

## 🔗 Tài liệu liên quan
- [README.md](README.md) - Kế hoạch triển khai chi tiết
