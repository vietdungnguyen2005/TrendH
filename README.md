# TREND HUNTER (DU KÍCH) — YÊU CẦU & KẾ HOẠCH TRIỂN KHAI CHI TIẾT

> Tài liệu này là "bản hướng dẫn triển khai" cho dự án Trend Hunter (Du Kích). Nó mô tả yêu cầu, kiến trúc, quy trình kỹ thuật, kế hoạch thực thi theo milestone, tiêu chí kiểm thử và vận hành. **Không chứa code** — chỉ lộ trình và checklist thực thi.

---

## 1. Mục tiêu dự án
- Phát hiện sớm (lead time: giờ → vài ngày) các từ khóa/sản phẩm **có khả năng trở thành trend** trong micro-niche.
- Ưu tiên **precision** (ít cảnh báo rác) để hỗ trợ quyết định kinh doanh (marketing, nhập hàng, content). 
- Chạy được trong môi trường chi phí thấp: laptop hoặc VPS nhỏ, tối ưu RAM/CPU.

---

## 2. Phạm vi công việc (Scope)
**Bao gồm:**
- Thu thập dữ liệu: Reddit, TikTok Creative Center, (giai đoạn sau: Pinterest, Twitter). 
- Lọc & trích xuất: rule-based + lightweight NLP.
- Xác minh: Google Trends (pytrends) với replicate sampling.
- Scoring: rule-based scoring (phi-ML giai đoạn 1), ML chỉ dùng sau có dữ liệu đủ.
- Backtest & KPI reporting.
- Dashboard (Streamlit) + alert (Telegram/email).

**Không bao gồm (giai đoạn ban đầu):**
- Mô hình LLM lớn (chạy inference liên tục), hệ thống phân phối đa vùng.

---

## 3. Yêu cầu chi tiết

### 3.1 Yêu cầu chức năng (Functional)
1. Crawler thu thập posts từ danh sách subreddit và TikTok hashtag list theo lịch.  
2. Bộ lọc loại bỏ spam, quảng cáo, tin tức chính trị (blacklist).  
3. Trích xuất cụm từ/từ khoá tiềm năng (entity candidates) và chuẩn hoá variant.  
4. Wrapper pytrends: gọi Google Trends theo batch, replicate n=3, lưu raw + median series.  
5. Tính toán features: slope, acceleration, moving average, platform_count, novelty_score.  
6. Scoring engine: rule-based weight formula trả về `TrendScore` + nhãn (Hidden Gem / Breakout / Stable / Dying).  
7. Backtest runner: running rolling-window evaluation, xuất báo cáo Precision@K, Recall, Lead Time.  
8. UI: Streamlit dashboard hiển thị top flags, chart IOT + mentions, raw posts, export CSV.  
9. Alerts: gửi Telegram/email cho flags high-confidence.

### 3.2 Yêu cầu phi chức năng (Non-functional)
- **Tài nguyên:** phải chạy trên laptop 8–16GB RAM hoặc VPS (2–4 vCPU, 4–8GB RAM).  
- **Độ trễ:** pipeline batch chạy hourly (hoặc configurable).  
- **Độ sẵn sàng:** ổn định 99% đối với job scheduler; log chi tiết cho debug.  
- **Bảo mật & pháp lý:** tuân thủ ToS nền tảng; không lưu dữ liệu nhạy cảm; rate-limit theo quy định.

---

## 4. Kiến trúc kỹ thuật (high-level)
- **Ingest Layer:** Crawlers (Reddit JSON, Playwright TikTok) → `sources_raw`.
- **Processing Layer:** Filtering → Entity extraction → Normalization → `keywords` canonical table.
- **Verification Layer:** pytrends wrapper (replicate + median) → `time_series_metrics`.
- **Feature Layer:** Feature engineering pipeline (vectorized pandas) → `features` table.
- **Scoring Layer:** Rule-based Scorer → `flags` table.
- **Backtest & Model Layer:** Rolling-window backtest → (optionally) training LightGBM after đủ data.
- **UI & Alerts:** Streamlit app + Telegram/SMTP.
- **Storage:** SQLite for PoC → PostgreSQL khi scale.

---

## 5. Dữ liệu & schema tối thiểu
**Bảng `sources_raw`**: id, timestamp, source, author, text, meta_json

**Bảng `keywords`**: id, canonical_term, variants_json, first_seen

**Bảng `time_series_metrics`**: id, term_id, date_time, iot_value, mentions_reddit, mentions_tiktok, platform_count, raw_samples_json

**Bảng `features`**: id, term_id, date_time, slope, acceleration, ma3, ma7, pct_change_24h, novelty_score, influencer_weighted_mentions

**Bảng `flags`**: id, term_id, date_time, trend_score, label, reason_codes, alert_sent

---

## 6. Kế hoạch triển khai theo milestone (chi tiết)
> Mỗi milestone gồm mục tiêu, deliverables, kiểm thử, chuẩn chấp thuận (acceptance).

### Milestone 0 — Chuẩn bị môi trường (Day 0)
**Mục tiêu:** thành lập môi trường dev, DB, scheduler, repo.
**Deliverables:** repo Git, venv, requirements.txt, SQLite init script, cron template.
**Kiểm thử:** scripts khởi tạo DB chạy thành công.
**Accept:** sẵn sàng chạy crawler mock.

### Milestone 1 — MVP Crawler + Storage (Week 1)
**Mục tiêu:** thu thập data từ 5 subreddit + 1 TikTok list, lưu `sources_raw`.
**Deliverables:** crawler/reddit.py, crawler/tiktok.py (scrape/JSON), scripts scheduler.
**Kiểm thử:** xác thực schema `sources_raw`; KPI: items_collected_per_run >= 100; failed_rate <5%.
**Accept:** có dữ liệu thô liên tục 48 giờ.

### Milestone 2 — Filtering & Entity Extraction (Week 1–2)
**Mục tiêu:** pipeline lọc rule-based, trích entity, canonical mapping.
**Deliverables:** filtering.py, entity_extraction.py, keywords table population.
**Kiểm thử:** sample audit 500 items: false_drop_rate ≤ 10%; variant grouping purity ≥ 85%.
**Accept:** danh sách canonical keywords mỗi ngày ≥ 1k.

### Milestone 3 — Pytrends Wrapper & Verification (Week 2)
**Mục tiêu:** triển khai replicate sampling + caching.
**Deliverables:** pytrends_wrapper.py, cache layer, raw samples persisted.
**Kiểm thử:** run 100 terms: successful_pytrends_calls_rate ≥ 95%; caching_hit_rate > 60%.
**Accept:** median IOT series cho mỗi term có sẵn.

### Milestone 4 — Feature Engineering & Scoring Rules (Week 2–3)
**Mục tiêu:** tính slope, acceleration, platform_count, novelty_score; chốt scoring formula.
**Deliverables:** feature_engineering.py, scoring config (weights), flags generation.
**Kiểm thử:** sanity histograms, feature_coverage ≥ 95%, scoring top-100 reasonable (manual check).
**Accept:** top-50 flags có 50%+ chất lượng theo kiểm tra manual (mục tiêu Precision cao).

### Milestone 5 — Backtest Framework (Week 3–4)
**Mục tiêu:** rolling-window backtest; tune thresholds to meet Precision@K target.
**Deliverables:** backtest/rolling_cv.py, backtest reports (Precision@50/100, recall, lead-time distribution).
**Kiểm thử:** chạy backtest trên toàn bộ data lịch sử đã thu thập (≥ 2–4 tuần). 
**Accept:** threshold được quyết định cho production.

### Milestone 6 — UI & Alerts (Week 4)
**Mục tiêu:** Streamlit dashboard, export CSV, Telegram alert.
**Deliverables:** app.py, config alerts, documentation user.
**Kiểm thử:** manual end-to-end test (flag -> alert delivered).
**Accept:** stakeholder xác nhận dashboard hữu dụng.

### Milestone 7 — Hardening & Ops (Week 5)
**Mục tiêu:** caching, retry/backoff, IP reset script, logging rotation, backup.
**Deliverables:** ip_reset.py, retry utils, log rotation, DB backup script.
**Kiểm thử:** simulate 429 events, verify auto-throttle and fallback behaviors.
**Accept:** system chịu đựng spike requests mà không crash.

### Milestone 8 — Optional: ML Re-ranker (Month 2+) 
**Mục tiêu:** khi có ≥ 1 tháng data và ground-truth, huấn luyện LightGBM re-ranker.
**Deliverables:** train_model.py, model artifacts, eval report.
**Kiểm thử:** k-fold / rolling CV; model improves Precision@K trên baseline score.
**Accept:** model đưa vào production A/B test.

---

## 7. Backtest & Định nghĩa ground-truth (chi tiết)
**Định nghĩa ground-truth (gợi ý):** 1 term được coi là "trend" nếu trong vòng 7 ngày sau khi flag: 
- Google Trends IOT tăng ≥ T_percent (ví dụ 100% so với baseline 14 ngày) **và** absolute IOT > X; hoặc
- Term xuất hiện trong top-50 TikTok hashtags hoặc top-10 posts Reddit trong khung 72h.

**Backtest protocol:**
- Dùng rolling-window (ví dụ train/validate windows: 14-day training, next 7-day test). Không dùng random split.
- Metrics: Precision@50, Precision@100, Recall@7d, Median lead-time (hours), FPR.
- Calibration: điều chỉnh scoring threshold trên validation windows để meet Precision@K.

**Artifacts cần lưu:** raw samples, computed features, flags, ground-truth labels, model checkpoints,.

---

## 8. KPI & báo cáo (hằng ngày / hằng tuần)
**Daily:** ingestion_count, flags_count, Precision@50 (sample human-audit), failed_requests_rate, 429_count

**Weekly:** Precision@100, Recall_7d, Median lead time, top 10 hits (case studies), system uptime

**Monthly:** trend_capture_rate (so với đối thủ hoặc benchmark), cost per flag, dataset growth

---

## 9. Giám sát & kế hoạch xử lý sự cố
**Logs:** structured JSON logs cho từng job (timestamp, job_id, status, error)

**Alert rules:**
- 429_count > threshold trong 1 giờ -> suspend heavy queries, trigger ip_reset.
- ingestion_count < expected -> send urgent alert.
- backtest_precision giảm > 10% so với baseline -> warn data drift.

**Sao lưu:** DB dump daily; raw data snapshot weekly.

---

## 10. Rủi ro chính & phương án giảm thiểu
1. **Google block / 429**: batch small, replicate=3, cache 24h, IP rotate (Dcom reset) — fallback: rely social-only until unblocked.
2. **Base-rate thấp (nhiều false positives)**: tập trung precision bằng scoring công thức; giảm số flag bằng threshold cao; manual audit loop.
3. **Data drift / concept drift**: monitor feature distributions, retrain / recalibrate weekly.
4. **Overfiltering**: giữ sample human-audit 1% để phát hiện false drop.
5. **Legal/ToS risk**: đọc & tuân thủ ToS nền tảng; tránh scraping cấm; dùng Creative Center/public endpoints.

---

## 11. Tài nguyên & ước tính chi phí
**Phần cứng:** laptop 8–16GB RAM (0đ nếu sẵn), hoặc VPS (tùy chọn) ~100k–400k VND/tháng
**SIM 4G (IP rotate):** ~150k VND/tháng (tuỳ gói)
**Chi phí phát triển:** 1 dev part-time => timeline 4–6 tuần MVP
**Lưu trữ:** SQLite local (0đ) → PostgreSQL khi scale (chi phí VPS/storage)

---

## 12. Checklist nghiệm thu (Pre-production)
- [ ] Crawler chạy hourly, dữ liệu raw lưu ≥ 48h
- [ ] Filtering false_drop_rate ≤ 10% (sample 500)
- [ ] Pytrends wrapper trả median series, caching hoạt động
- [ ] Feature coverage ≥ 95%
- [ ] Scoring thresholds calibrated (Precision@50 target đạt)
- [ ] Dashboard hiển thị & alert tested
- [ ] Backups và logs đã thiết lập

---

## 13. Các bước tiếp theo (gợi ý ưu tiên)
1. Triển khai Milestone 0 → 1 → 2 liên tiếp để có pipeline cơ bản trong 7–10 ngày.  
2. Chạy real-time 2 tuần, thu data để đánh giá base-rate & refine blacklist/weights.  
3. Thiết lập backtest rolling window và quyết threshold.  
4. Sau 1 tháng, cân nhắc thêm ML re-ranker nếu volume & labels đủ.

---

## 14. Phụ lục — Mẫu cấu hình scoring (tham khảo)
**Normalized features:** tất cả feature chuẩn hóa về 0..1 theo sliding-window historical percentiles.

**Gợi ý trọng số ban đầu:**
- normalized_slope: 0.35
- platform_count (capped at 3): 0.25
- growth_rate_social: 0.20
- novelty_score: 0.20

**Luật bổ trợ:** platform_count >= 2 và normalized_slope > 0.3 → label = Breakout candidate (high-confidence)

---



***Kết thúc tài liệu.***
