# youtube_agent.py
import json
import time
from datetime import datetime, timedelta, timezone
import schedule
import requests
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os

# ====================== CẤU HÌNH ======================
API_KEY = "<API Youtube>"  # Dùng tạm, sau chuyển .env
DATA_FILE = "streams_data.json"

KEYWORDS_FILTER = [
    "AI", "Automation", "Tokenization", "Crypto",
    "Blockchain", "Fintech", "Web3", "Headhunter"
]  # Từ khóa lọc

MESSAGE_TEMPLATES = {
    "live": """{service} with USD $900Trillion+ added value from Option Leadership
Let’s transform your {service} to your equity by leveraging tokenization + cross-border payment + climate change Compound Options to accelerate your startup’s growth.

With a funding cost of 15+% for amounts under USD $10Billion (minimum USD $1 Million), we provide a highly efficient way to secure venture capital while maximizing scalability.

With not only your funding target but also your ANY targets, the SIGNIFICANTLY efficient way is donating to TAHK #Foundation for enjoying USD $900+ trillion option leadership then we will help you:
- Donating $150 thousand USD per year service.
- Email to: donate@tahkfoundation.org for your #donation.

As an Universal Interacting & Media Solutions nonprofit, TAHK Foundation will help you interact with the best options for your requirements.""",

    "upcoming": """Upcoming {service} with USD $900Trillion+ added value from Option Leadership
Let’s transform your {service} to your equity by leveraging tokenization + cross-border payment + climate change Compound Options..."""
}

# Load OAuth (token.pickle từ trước)
def get_youtube_client():
    try:
        import pickle
        with open("token.pickle", "rb") as f:
            credentials = pickle.load(f)
        return build("youtube", "v3", credentials=credentials)
    except:
        print("❌ Chưa có token! Chạy youtube_token.py trước.")
        exit()

youtube = get_youtube_client()

# ====================== FETCHER ======================
def fetch_streams(query="live OR upcoming", max_results=30):
    url = "https://www.googleapis.com/youtube/v3/search"
    streams = []
    
    for event_type in ["live", "upcoming"]:
        params = {
            "part": "snippet",
            "eventType": event_type,
            "type": "video",
            "q": query,
            "maxResults": max_results,
            "key": API_KEY,
            "order": "relevance"
        }
        
        try:
            resp = requests.get(url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            
            for item in data.get("items", []):
                video_id = item["id"]["videoId"]
                snippet = item["snippet"]
                
                # Lấy thêm scheduledStartTime
                details = get_stream_details(video_id)
                
                streams.append({
                    "video_id": video_id,
                    "title": snippet["title"],
                    "channel": snippet["channelTitle"],
                    "published_at": snippet["publishedAt"],
                    "status": event_type,
                    "scheduled_start": details.get("scheduledStartTime"),
                    "thumbnail": snippet["thumbnails"]["medium"]["url"],
                    "processed": False
                })
        except Exception as e:
            print(f"Lỗi fetch {event_type}: {e}")
    
    # Lưu vào file
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(streams, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Đã lưu {len(streams)} stream vào {DATA_FILE}")
    return streams

def get_stream_details(video_id):
    try:
        resp = youtube.videos().list(
            part="liveStreamingDetails",
            id=video_id
        ).execute()
        items = resp.get("items", [])
        if items:
            details = items[0].get("liveStreamingDetails", {})
            return {
                "scheduledStartTime": details.get("scheduledStartTime"),
                "activeLiveChatId": details.get("activeLiveChatId")
            }
    except:
        pass
    return {}

# ====================== PROCESSOR (AI AGENT) ======================
def load_streams():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def should_process(stream, filter_keywords):
    title_lower = stream["title"].lower()
    return any(kw.lower() in title_lower for kw in filter_keywords)

def generate_message(stream):
    title = stream["title"].strip()
    
    # === Tự động phát hiện chủ đề (Tên service) ===
    service = detect_service_from_title(title)
    
    # Nếu không detect được thì dùng tiêu đề rút gọn
    if not service:
        service = title[:60] + "..." if len(title) > 60 else title
    
    template = MESSAGE_TEMPLATES.get(stream["status"], MESSAGE_TEMPLATES["live"])
    
    # Thay thế {service}
    message = template.format(service=service)
    return message


def detect_service_from_title(title: str) -> str:
    """Tự động trích xuất chủ đề từ tiêu đề livestream"""
    title_lower = title.lower()
    
    # Danh sách mapping từ khóa → Tên service
    service_map = {
        "ai": "AI & Automation",
        "artificial intelligence": "AI & Automation",
        "automation": "AI & Automation",
        "fintech": "Fintech & Cross-border Payment",
        "crypto": "Crypto & Tokenization",
        "blockchain": "Crypto & Tokenization",
        "tokenization": "Tokenization",
        "payment": "Cross-border Payment",
        "charity": "Charity & Philanthropy",
        "donation": "Charity & Philanthropy",
        "headhunter": "Headhunter & Recruitment",
        "startup": "Startup Growth",
        "funding": "Venture Funding",
    }
    
    for keyword, service_name in service_map.items():
        if keyword in title_lower:
            return service_name
    
    # Nếu không match từ khóa, trả về cụm từ đầu tiên của title
    words = title.split()
    if len(words) >= 3:
        return " ".join(words[:4])  # Lấy 4 từ đầu tiên
    return title

def send_message(live_chat_id, message):
    try:
        youtube.liveChatMessages().insert(
            part="snippet",
            body={
                "snippet": {
                    "liveChatId": live_chat_id,
                    "type": "textMessageEvent",
                    "textMessageDetails": {"messageText": message}
                }
            }
        ).execute()
        return True
    except HttpError as e:
        error_str = str(e)
        if "insufficient permissions" in error_str or "403" in error_str:
            print(f"   ⚠️ Không có quyền gửi tin nhắn (403)")
        elif "invalid" in error_str.lower():
            print(f"   ⚠️ Chat không hợp lệ hoặc chưa sẵn sàng (400)")
        else:
            print(f"   ❌ Lỗi gửi tin: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Lỗi không xác định: {e}")
        return False

def process_stream(stream):
    if stream.get("processed", False):
        return
    
    try:
        details = get_stream_details(stream["video_id"])
        live_chat_id = details.get("activeLiveChatId")
        
        if not live_chat_id:
            # print(f"   ⚠️ Không có live chat: {stream['title'][:60]}")
            return

        # Xử lý gửi tin nhắn
        if stream["status"] == "live":
            msg = generate_message(stream)
            if send_message(live_chat_id, msg):
                print(f"✅ Đã gửi tin nhắn LIVE: {stream['title'][:80]}")
                stream["processed"] = True
            else:
                stream["processed"] = False  # Cho thử lại sau

        elif stream["status"] == "upcoming" and stream.get("scheduled_start"):
            # Sửa lỗi datetime
            scheduled_str = stream["scheduled_start"]
            if scheduled_str.endswith('Z'):
                scheduled = datetime.fromisoformat(scheduled_str.replace('Z', '+00:00'))
            else:
                scheduled = datetime.fromisoformat(scheduled_str)
            
            now = datetime.now(timezone.utc)
            
            # Gửi trước khoảng 10-15 phút
            if now >= scheduled - timedelta(minutes=15):
                msg = generate_message(stream)
                if send_message(live_chat_id, msg):
                    print(f"✅ Đã gửi tin nhắn UPCOMING: {stream['title'][:80]}")
                    stream["processed"] = True
    except Exception as e:
        print(f"   ❌ Lỗi xử lý stream {stream['title'][:50]}: {e}")

# ====================== MAIN LOOP (ĐÃ SỬA) ======================
def main_loop():
    print("🤖 AI Agent YouTube đang chạy...")
    last_fetch = 0
    
    while True:
        try:
            current_time = time.time()
            
            # Chỉ fetch dữ liệu mỗi 60 giây một lần (tránh spam)
            if current_time - last_fetch > 60:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Đang cập nhật danh sách stream...")
                fetch_streams()          # Cập nhật dữ liệu
                last_fetch = current_time
            
            streams = load_streams()
            matched_count = 0
            
            print(f"→ Đang kiểm tra {len(streams)} stream...")
            
            for stream in streams:
                title = stream["title"]
                if should_process(stream, KEYWORDS_FILTER):
                    matched_count += 1
                    print(f"   🔍 PHÙ HỢP: {title[:80]}... | Status: {stream['status']} | Channel: {stream['channel']}")
                    process_stream(stream)
            
            if matched_count == 0:
                print(f"   → Không tìm thấy stream nào khớp với từ khóa.")
                # In thử 3 stream phổ biến nhất để bạn xem
                print(f"   📋 Một số stream đang có:")
                for s in streams[:3]:
                    print(f"      • {s['title'][:70]}... ({s['status']})")
            
            # Lưu lại trạng thái processed
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(streams, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"Lỗi vòng lặp: {e}")
        
        time.sleep(20)   # Kiểm tra mỗi 20 giây (nhanh để phát hiện upcoming)


if __name__ == "__main__":
    main_loop()   # Không dùng schedule nữa để tránh xung đột