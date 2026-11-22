"""
Tạo file Excel bảng khảo sát góc ngồi thực nghiệm — Phúc (Nhóm Training AI)
Chạy: python create_survey_excel.py
"""

from openpyxl import Workbook
from openpyxl.styles import (
    PatternFill, Font, Alignment, Border, Side
)
from openpyxl.utils import get_column_letter

OUTPUT_FILE = "Khao_Sat_Goc_Ngoi_ThucNghiem.xlsx"

# ── Màu sắc ──
COLOR_HEADER_BLUE   = "1F4E79"  # tiêu đề chính
COLOR_HEADER_LIGHT  = "BDD7EE"  # tiêu đề phụ
COLOR_POSTURE       = "DDEBF7"  # nhóm tư thế
COLOR_ATTENTION     = "E2EFDA"  # nhóm chú ý
COLOR_THRESHOLD     = "FFF2CC"  # hàng ngưỡng
COLOR_NOTE          = "F4CCCC"  # ghi chú cảnh báo
COLOR_WHITE         = "FFFFFF"
COLOR_GRAY          = "F2F2F2"

def border(style="thin"):
    s = Side(style=style)
    return Border(left=s, right=s, top=s, bottom=s)

def header_font(bold=True, white=True, size=11):
    return Font(bold=bold, color="FFFFFF" if white else "000000", size=size)

def fill(hex_color):
    return PatternFill("solid", fgColor=hex_color)

def center():
    return Alignment(horizontal="center", vertical="center", wrap_text=True)

def left():
    return Alignment(horizontal="left", vertical="center", wrap_text=True)


wb = Workbook()

# ════════════════════════════════════════════════
# SHEET 1 — Khảo sát tư thế (main_monitor.py)
# ════════════════════════════════════════════════
ws1 = wb.active
ws1.title = "Tư Thế Ngồi"

# Tiêu đề lớn
ws1.merge_cells("A1:K1")
ws1["A1"] = "BẢNG KHẢO SÁT TƯ THẾ NGỒI THỰC NGHIỆM — NHÓM TRAINING AI (PHÚC)"
ws1["A1"].font = Font(bold=True, color="FFFFFF", size=13)
ws1["A1"].fill = fill(COLOR_HEADER_BLUE)
ws1["A1"].alignment = center()
ws1.row_dimensions[1].height = 30

# Thông tin chung
ws1.merge_cells("A2:K2")
ws1["A2"] = "Công cụ: main_monitor.py + test_attention.py  |  Ngày khảo sát: ___/___/2026  |  Người thực hiện: Phan Hà Minh Phúc"
ws1["A2"].font = Font(italic=True, size=10)
ws1["A2"].fill = fill(COLOR_GRAY)
ws1["A2"].alignment = left()
ws1.row_dimensions[2].height = 18

ws1.append([])  # dòng trống

# ── Tiêu đề ngưỡng hiện tại ──
ws1.merge_cells("A4:K4")
ws1["A4"] = "⚙️  NGƯỠNG HIỆN TẠI TRONG CODE (cần kiểm tra có phù hợp thực tế không)"
ws1["A4"].font = Font(bold=True, size=10)
ws1["A4"].fill = fill(COLOR_THRESHOLD)
ws1["A4"].alignment = left()

threshold_headers = ["Chỉ số", "Ngưỡng code", "Ý nghĩa"]
threshold_data = [
    ["Neck Tilt",      "> 25°",        "Gập cổ — cúi đầu quá sát vở"],
    ["Shoulder Tilt",  "> 10°",        "Lệch vai — nguy cơ vẹo cột sống"],
    ["Head drop",      "> 60% màn hình","Cúi quá sát bàn (< 25 cm)"],
    ["EAR mắt",        "< 0.20",       "Nhắm mắt — buồn ngủ"],
    ["Yaw quay đầu",   "< 0.28 hoặc > 0.72", "Nhìn sang hướng khác > 5 giây"],
]
ws1.append(threshold_headers)
for cell, col in zip(ws1[5], ["A","B","C"]):
    cell.font = Font(bold=True, color="FFFFFF")
    cell.fill = fill("7F6000")
    cell.alignment = center()
    cell.border = border()

for row_data in threshold_data:
    ws1.append(row_data)
    r = ws1.max_row
    for col in range(1, 4):
        ws1.cell(r, col).fill = fill(COLOR_THRESHOLD)
        ws1.cell(r, col).border = border()
        ws1.cell(r, col).alignment = center()

ws1.append([])  # dòng trống

# ── Header bảng đo chính ──
r_header = ws1.max_row + 1
ws1.merge_cells(f"A{r_header}:K{r_header}")
ws1[f"A{r_header}"] = "📋  BẢNG GHI SỐ LIỆU ĐO THỰC NGHIỆM"
ws1[f"A{r_header}"].font = Font(bold=True, color="FFFFFF", size=11)
ws1[f"A{r_header}"].fill = fill(COLOR_HEADER_BLUE)
ws1[f"A{r_header}"].alignment = center()
ws1.row_dimensions[r_header].height = 22

r_col = r_header + 1
col_headers = [
    "STT",
    "Tên người\nkhảo sát",
    "Tư thế thực hiện",
    "Neck Tilt\nđo được (°)",
    "Shoulder Tilt\nđo được (°)",
    "State hiển thị\n(GOOD/WARNING/ALERT)",
    "EAR trung bình\n(mắt mở)",
    "EAR khi\nnhắm mắt",
    "Yaw ratio\n(nhìn thẳng)",
    "FPS\ntrung bình",
    "Ghi chú"
]
ws1.append(col_headers)
ws1.row_dimensions[r_col].height = 40
for col_idx, cell in enumerate(ws1[r_col], 1):
    cell.font = Font(bold=True, color="FFFFFF", size=10)
    cell.fill = fill("2E75B6")
    cell.alignment = center()
    cell.border = border()

# ── Dữ liệu mẫu: 5 người × 4 tư thế ──
postures = [
    "Ngồi thẳng bình thường",
    "Cúi đầu đọc sách/vở",
    "Vẹo vai (chống khuỷu tay)",
    "Cúi sát mặt bàn",
]

stt = 1
for person_idx in range(1, 6):
    person_name = f"Người {person_idx}"
    for p_idx, posture in enumerate(postures):
        row = [
            stt,
            person_name if p_idx == 0 else "",  # gộp ô tên theo nhóm
            posture,
            "",  # Neck Tilt
            "",  # Shoulder Tilt
            "",  # State
            "" if posture != "Ngồi thẳng bình thường" else "",
            "",  # EAR nhắm
            "",  # Yaw
            "",  # FPS
            "",  # Ghi chú
        ]
        ws1.append(row)
        r = ws1.max_row
        row_color = COLOR_POSTURE if person_idx % 2 == 1 else COLOR_WHITE
        for col_idx in range(1, 12):
            cell = ws1.cell(r, col_idx)
            cell.border = border()
            cell.alignment = center()
            if col_idx not in [3, 11]:  # cột tư thế và ghi chú căn trái
                cell.alignment = center()
            else:
                cell.alignment = left()
            if col_idx <= 2:
                cell.fill = fill(row_color)
            elif col_idx == 3:
                cell.fill = fill(COLOR_POSTURE if person_idx % 2 == 1 else COLOR_GRAY)
        stt += 1
    # Dòng trống giữa các người
    ws1.append([""] * 11)

ws1.append([])

# ── Bảng tổng hợp ngưỡng đề xuất ──
ws1.merge_cells(f"A{ws1.max_row + 1}:K{ws1.max_row + 1}")
r_sum = ws1.max_row
ws1[f"A{r_sum}"] = "📝  TỔNG HỢP & ĐỀ XUẤT CHỈNH NGƯỠNG SAU KHẢO SÁT"
ws1[f"A{r_sum}"].font = Font(bold=True, color="FFFFFF", size=11)
ws1[f"A{r_sum}"].fill = fill("375623")
ws1[f"A{r_sum}"].alignment = center()

suggest_headers = ["Chỉ số", "Ngưỡng cũ (code)", "Giá trị TB thực tế", "Đề xuất ngưỡng mới", "Lý do"]
ws1.append(suggest_headers)
r = ws1.max_row
for col_idx, cell in enumerate(ws1[r], 1):
    cell.font = Font(bold=True, color="FFFFFF")
    cell.fill = fill("538135")
    cell.alignment = center()
    cell.border = border()

for label, old in [
    ("Neck Tilt", "> 25°"),
    ("Shoulder Tilt", "> 10°"),
    ("EAR nhắm mắt", "< 0.20"),
    ("Yaw quay đầu", "< 0.28 / > 0.72"),
]:
    ws1.append([label, old, "", "", ""])
    r = ws1.max_row
    for col_idx in range(1, 6):
        ws1.cell(r, col_idx).fill = fill(COLOR_ATTENTION)
        ws1.cell(r, col_idx).border = border()
        ws1.cell(r, col_idx).alignment = center()

# ── Độ rộng cột ──
col_widths = [5, 16, 28, 14, 14, 24, 14, 14, 16, 10, 20]
for i, w in enumerate(col_widths, 1):
    ws1.column_dimensions[get_column_letter(i)].width = w


# ════════════════════════════════════════════════
# SHEET 2 — Ghi chú hướng dẫn
# ════════════════════════════════════════════════
ws2 = wb.create_sheet("Hướng Dẫn")

guide = [
    ("HƯỚNG DẪN SỬ DỤNG BẢNG KHẢO SÁT", True, COLOR_HEADER_BLUE, True),
    ("", False, COLOR_WHITE, False),
    ("BƯỚC 1 — Chuẩn bị", True, "2E75B6", True),
    ("- Mở terminal: cd ai  →  .\\venv\\Scripts\\activate", False, COLOR_GRAY, False),
    ("- Chạy: python main_monitor.py", False, COLOR_GRAY, False),
    ("", False, COLOR_WHITE, False),
    ("BƯỚC 2 — Đo tư thế (Sheet 'Tư Thế Ngồi')", True, "2E75B6", True),
    ("- Mời từng bạn ngồi trước camera", False, COLOR_GRAY, False),
    ("- Yêu cầu thực hiện lần lượt 4 tư thế, đọc số trên màn hình rồi điền vào bảng", False, COLOR_GRAY, False),
    ("- Cột 'State': ghi GOOD / WARNING_PENDING / ALERT_TRIGGERED", False, COLOR_GRAY, False),
    ("", False, COLOR_WHITE, False),
    ("BƯỚC 3 — Đo chú ý", True, "2E75B6", True),
    ("- Nhấn q đóng main_monitor.py", False, COLOR_GRAY, False),
    ("- Chạy: python test_attention.py", False, COLOR_GRAY, False),
    ("- Yêu cầu bạn: mắt mở bình thường → ghi EAR", False, COLOR_GRAY, False),
    ("- Yêu cầu bạn: nhắm mắt từ từ → ghi EAR khi nhắm", False, COLOR_GRAY, False),
    ("- Yêu cầu bạn: quay đầu sang trái/phải → ghi Yaw ratio", False, COLOR_GRAY, False),
    ("", False, COLOR_WHITE, False),
    ("BƯỚC 4 — Điền bảng tổng hợp", True, "2E75B6", True),
    ("- Tính trung bình các số đo được", False, COLOR_GRAY, False),
    ("- Điền vào bảng 'Đề xuất ngưỡng mới' ở cuối sheet", False, COLOR_GRAY, False),
    ("- Viết lý do nếu đề xuất thay đổi ngưỡng", False, COLOR_GRAY, False),
    ("", False, COLOR_WHITE, False),
    ("LƯU Ý QUAN TRỌNG", True, "C00000", True),
    ("- Không chụp ảnh khuôn mặt bạn — chỉ ghi số liệu vào bảng này", False, COLOR_NOTE, False),
    ("- Không commit file Excel này lên Git", False, COLOR_NOTE, False),
    ("- File này chỉ dùng nội bộ nhóm và nộp báo cáo cho thầy", False, COLOR_NOTE, False),
]

ws2.column_dimensions["A"].width = 80
for text, bold, bg, white_text in guide:
    ws2.append([text])
    r = ws2.max_row
    ws2.row_dimensions[r].height = 20
    cell = ws2.cell(r, 1)
    cell.font = Font(bold=bold, color="FFFFFF" if white_text else "000000", size=11)
    cell.fill = fill(bg)
    cell.alignment = left()


wb.save(OUTPUT_FILE)
print(f"✅ Đã tạo file: {OUTPUT_FILE}")
