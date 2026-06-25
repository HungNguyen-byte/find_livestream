# youtube_filter.py
import json
import pandas as pd
from datetime import datetime, timedelta, timezone
import os

DATA_FILE = "streams_data.json"
OUTPUT_EXCEL = "upcoming_streams.xlsx"

def load_and_clean_streams():
    """Đọc và làm sạch dữ liệu từ JSON"""
    if not os.path.exists(DATA_FILE):
        print(f"❌ Không tìm thấy file {DATA_FILE}")
        return []
    
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        streams = json.load(f)
    
    cleaned = []
    for stream in streams:
        if stream.get("status") != "upcoming":
            continue  # Chỉ lấy upcoming
            
        # Làm sạch dữ liệu
        scheduled_str = stream.get("scheduled_start")
        scheduled_time = None
        
        if scheduled_str:
            try:
                if scheduled_str.endswith('Z'):
                    scheduled_time = datetime.fromisoformat(scheduled_str.replace('Z', '+00:00'))
                else:
                    scheduled_time = datetime.fromisoformat(scheduled_str)
                scheduled_time = scheduled_time.astimezone(timezone.utc)
            except:
                pass
        
        cleaned.append({
            "Video ID": stream.get("video_id"),
            "Title": stream.get("title", ""),
            "Channel": stream.get("channel", ""),
            "Scheduled Start (UTC)": scheduled_time,
            "Scheduled Start (VN)": scheduled_time + timedelta(hours=7) if scheduled_time else None,
            "Status": stream.get("status"),
            "Thumbnail": stream.get("thumbnail", ""),
            "Published At": stream.get("published_at", ""),
        })
    
    print(f"✅ Đã làm sạch và lọc được {len(cleaned)} stream upcoming.")
    return cleaned


def filter_by_date(streams, days_ahead=7):
    """Lọc theo ngày (mặc định lấy 7 ngày tới)"""
    now = datetime.now(timezone.utc)
    end_date = now + timedelta(days=days_ahead)
    
    filtered = []
    for stream in streams:
        if stream["Scheduled Start (UTC)"]:
            if now <= stream["Scheduled Start (UTC)"] <= end_date:
                filtered.append(stream)
    
    print(f"✅ Lọc theo {days_ahead} ngày tới: còn {len(filtered)} stream.")
    return filtered


def export_to_excel(streams, filename=OUTPUT_EXCEL):
    """Xuất ra file Excel"""
    if not streams:
        print("⚠️ Không có dữ liệu để xuất Excel.")
        return
    
    df = pd.DataFrame(streams)
    
    # Sắp xếp theo thời gian
    df = df.sort_values(by="Scheduled Start (UTC)")
    
    # Định dạng cột thời gian
    df["Scheduled Start (UTC)"] = pd.to_datetime(df["Scheduled Start (UTC)"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    df["Scheduled Start (VN)"] = pd.to_datetime(df["Scheduled Start (VN)"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    
    df.to_excel(filename, index=False, engine='openpyxl')
    
    print(f"✅ Đã xuất file Excel thành công: **{filename}**")
    print(f"   Số lượng stream: {len(df)}")


def main():
    print("🔧 YouTube Filter & Export Tool")
    print("=" * 50)
    
    # Load và clean
    streams = load_and_clean_streams()
    
    if streams:
        # Lọc theo ngày (bạn có thể thay đổi số ngày)
        filtered = filter_by_date(streams, days_ahead=10)  # Lấy 10 ngày tới
        
        # Xuất Excel
        export_to_excel(filtered)
        
        # Xuất thêm file JSON sạch (tùy chọn)
        with open("upcoming_cleaned.json", "w", encoding="utf-8") as f:
            json.dump(filtered, f, ensure_ascii=False, indent=2, default=str)
        print("✅ Đã xuất thêm upcoming_cleaned.json")
    else:
        print("⚠️ Không có stream upcoming nào.")


if __name__ == "__main__":
    main()