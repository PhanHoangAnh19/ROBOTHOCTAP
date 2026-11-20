import os
import sqlite3
import json
import urllib.request
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đặt key bằng biến môi trường, KHÔNG ghi key thẳng vào code:
#   PowerShell:  $env:GEMINI_API_KEY="..."
API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

def init_db():
    conn = sqlite3.connect("robot_events.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            event_type TEXT,
            category_name TEXT,
            detail TEXT,
            duration_minutes INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

init_db()

class AskPayload(BaseModel):
    question: str
    mode: str = "GIAI_TOAN" # GIAI_TOAN, DAY_HOC, THAC_MAC

class SensorEventPayload(BaseModel):
    event_type: str # TU_THE_CO, TU_THE_VAI, KHOANG_CACH_MAT, MAT_TAP_TRUNG
    detail: str

def log_event(event_type: str, category_name: str, detail: str, duration: int = 0):
    conn = sqlite3.connect("robot_events.db")
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO events (timestamp, event_type, category_name, detail, duration_minutes) VALUES (?, ?, ?, ?, ?)",
        (now, event_type, category_name, detail, duration)
    )
    conn.commit()
    conn.close()

# 1. API Học tập & Hỏi đáp đa chế độ (Toán học, Dạy học gợi mở, Trả lời thắc mắc)
@app.post("/ask-ai")
def ask_ai(payload: AskPayload):
    mode_prompts = {
        "GIAI_TOAN": ("Giải Toán", "Bạn là gia sư toán. Hãy giải chi tiết từng bước thật dễ hiểu dưới 60 từ:"),
        "DAY_HOC": ("Dạy Học Gợi Mở", "Bạn là gia sư Socratic. Đừng giải hộ ngay mà hãy gợi ý phương pháp tư duy dưới 60 từ:"),
        "THAC_MAC": ("Giải Đáp Kiến Thức", "Bạn là bách khoa toàn thư thông minh. Trả lời thú vị, ngắn gọn dưới 60 từ:")
    }
    
    cat_name, sys_prompt = mode_prompts.get(payload.mode, mode_prompts["THAC_MAC"])
    full_prompt = f"{sys_prompt} {payload.question}"
    
    try:
        data = {"contents": [{"parts": [{"text": full_prompt}]}]}
        req = urllib.request.Request(
            GEMINI_URL,
            data=json.dumps(data).encode("utf-8"),
            headers={"Content-Type": "application/json", "x-goog-api-key": API_KEY}
        )
        with urllib.request.urlopen(req, timeout=10) as res:
            result = json.loads(res.read().decode("utf-8"))
            answer = result["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        print(f"Lỗi gọi Gemini: {e}")
        answer = f"[Chế độ Offline] Đã nhận câu hỏi '{payload.question}'. (Kiểm tra lại API Key để AI trả lời thực tế)."
    log_event(payload.mode, cat_name, f"Hỏi: {payload.question} ➔ Đáp: {answer}", duration=5)
    return {"answer": answer}

# 2. API Ghi nhận đa dạng các loại cảnh báo từ Camera & AI Pose (Mục 3, 4)
@app.post("/sensor-event")
def sensor_event(payload: SensorEventPayload):
    category_map = {
        "TU_THE_CO": "Cảnh báo Gập Cổ",
        "TU_THE_VAI": "Cảnh báo Nghiêng Vai",
        "KHOANG_CACH_MAT": "Khoảng Cách Đầu - Bàn",
        "MAT_TAP_TRUNG": "Cảnh báo Mất Tập Trung"
    }
    cat_name = category_map.get(payload.event_type, "Cảnh báo Hệ Thống")
    log_event(payload.event_type, cat_name, payload.detail, duration=0)
    return {"status": "ok"}

# 3. API Lấy toàn bộ thống kê & sự kiện cho Dashboard (Mục 7, 8)
@app.get("/events")
def get_events():
    conn = sqlite3.connect("robot_events.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events ORDER BY id DESC LIMIT 50")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    total_minutes = sum(item["duration_minutes"] for item in rows)
    posture_warnings = sum(1 for item in rows if item["event_type"] in ["TU_THE_CO", "TU_THE_VAI", "KHOANG_CACH_MAT"])
    attention_warnings = sum(1 for item in rows if item["event_type"] == "MAT_TAP_TRUNG")
    ai_interactions = sum(1 for item in rows if item["event_type"] in ["GIAI_TOAN", "DAY_HOC", "THAC_MAC"])
    
    return {
        "summary": {
            "total_study_minutes": total_minutes,
            "posture_warnings": posture_warnings,
            "attention_warnings": attention_warnings,
            "ai_interactions": ai_interactions
        },
        "events": rows
    }