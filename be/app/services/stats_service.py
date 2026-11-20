# Tầng service: tính đúng thống kê cũ trên tối đa 50 sự kiện gần nhất.
from app.services import event_service


def dashboard(connection):
    rows = event_service.history(connection)
    summary = {
        "total_study_minutes": sum(row["duration_minutes"] for row in rows),
        "posture_warnings": sum(row["event_type"] in (
            "TU_THE_CO", "TU_THE_VAI", "KHOANG_CACH_MAT") for row in rows),
        "attention_warnings": sum(row["event_type"] == "MAT_TAP_TRUNG" for row in rows),
        "ai_interactions": sum(row["event_type"] in (
            "GIAI_TOAN", "DAY_HOC", "THAC_MAC") for row in rows),
    }
    return {"summary": summary, "events": rows}
