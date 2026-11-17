# Tầng dùng chung: tạo thời gian có múi giờ và định dạng tương thích dashboard.
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


def utc_now():
    return datetime.now(timezone.utc)


def legacy_timestamp(value: datetime, timezone_name: str):
    return value.astimezone(ZoneInfo(timezone_name)).strftime("%Y-%m-%d %H:%M:%S")
