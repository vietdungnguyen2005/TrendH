"""
Quick start script - Chạy toàn bộ pipeline một lần
"""

import subprocess
import sys
import time
from pathlib import Path


def run_command(cmd, description):
    """Run a command and show progress"""
    print(f"\n{'='*60}")
    print(f"▶️  {description}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        
        elapsed = time.time() - start_time
        print(result.stdout)
        print(f"✅ Hoàn thành trong {elapsed:.1f}s")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Lỗi: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        return False


def main():
    """Run complete pipeline"""
    print("\n🔥 TREND HUNTER - QUICK START 🔥\n")
    
    # Check if .env exists
    if not Path('.env').exists():
        print("⚠️  File .env không tồn tại!")
        print("   Tạo file .env từ .env.example và điền credentials")
        return 1
    
    steps = [
        ("python init_db.py", "1. Khởi tạo database"),
        ("python run_crawler.py", "2. Crawl dữ liệu từ Reddit/TikTok"),
        ("python run_processing.py", "3. Xử lý keywords"),
        ("python run_verification.py", "4. Lấy Google Trends data"),
        ("python run_features.py", "5. Tính features"),
        ("python run_scoring.py", "6. Chấm điểm trends"),
        ("python run_alerts.py", "7. Gửi alerts"),
        ("python show_status.py", "8. Hiển thị kết quả"),
    ]
    
    failed = []
    
    for cmd, desc in steps:
        if not run_command(cmd, desc):
            failed.append(desc)
            response = input(f"\n⚠️  Có lỗi xảy ra. Tiếp tục? (y/n): ")
            if response.lower() != 'y':
                break
    
    print("\n" + "="*60)
    print("📊 KẾT QUẢ")
    print("="*60)
    
    if not failed:
        print("✅ Tất cả bước đều thành công!")
        print("\n📌 Bước tiếp theo:")
        print("   1. Mở dashboard: python run_dashboard.py")
        print("   2. Hoặc chạy scheduler: python production_scheduler.py")
    else:
        print(f"❌ {len(failed)} bước thất bại:")
        for f in failed:
            print(f"   - {f}")
    
    print("="*60)
    
    return 0 if not failed else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
