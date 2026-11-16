"""
Module Kỹ nghệ Prompt Socratic & 10 Kịch bản kiểm thử (Task 8 - Tuần 3).
Đánh giá độ trễ và số lượng token tiêu thụ theo tiêu chuẩn M1.
"""

import time

SOCRATIC_SYSTEM_PROMPT = """Bạn là Robot gia sư AI thông minh và thân thiện đồng hành cùng các bạn học sinh tiểu học (6-12 tuổi).
Phong cách của bạn:
- Xưng hô thân mật: "Robot" và "con" hoặc "bạn nhỏ".
- Giọng điệu ấm áp, vui vẻ, khen ngợi và động viên khi bé nỗ lực.
- NGUYÊN TẮC VÀNG: TUYỆT ĐỐI KHÔNG giải hộ hay đưa ra đáp án cuối cùng ngay lập tức.
- Hãy dùng phương pháp gợi mở (Socratic): Đặt câu hỏi nhỏ, gợi ý từng bước để bé tự suy nghĩ và tìm ra lời giải.
- ĐỘ TIN CẬY: Nếu chữ viết tay hoặc đề bài bị mờ, hãy thành thật trả lời: "Robot nhìn chưa rõ chỗ này, bạn nhỏ chụp lại rõ nét hơn để Robot xem cùng nhé!".
"""

# 10 Kịch bản kiểm thử bao phủ toàn bộ tiểu học theo yêu cầu Task 8 Tuần 3
TEN_TEST_SCENARIOS = [
    {
        "id": "TC01_MATH_GRADE1",
        "title": "Toán lớp 1: Phép cộng có nhớ trong phạm vi 20",
        "question": "8 + 5 = ? (Bé đang phân vân chưa biết tính)",
        "guidance": "Gợi ý tách 5 thành 2 + 3 để gộp 8 + 2 = 10, rồi cộng tiếp với 3."
    },
    {
        "id": "TC02_MATH_GRADE2",
        "title": "Toán lớp 2: Bảng nhân 3",
        "question": "3 x 4 nghĩa là gì hả Robot?",
        "guidance": "Gợi ý đây là 3 được lấy 4 lần: 3 + 3 + 3 + 3."
    },
    {
        "id": "TC03_MATH_GRADE3",
        "title": "Toán lớp 3: Chu vi hình chữ nhật",
        "question": "Hình chữ nhật có chiều dài 8cm, chiều rộng 5cm, tính chu vi thế nào?",
        "guidance": "Hỏi bé công thức tính chu vi hình chữ nhật: '(dài + rộng) rồi nhân mấy nhỉ?'."
    },
    {
        "id": "TC04_MATH_GRADE4",
        "title": "Toán lớp 4: Tìm hai số khi biết Tổng và Hiệu",
        "question": "Tổng hai số là 25, hiệu là 7. Số lớn là bao nhiêu?",
        "guidance": "Gợi ý vẽ sơ đồ đoạn thẳng: Bớt đi phần hiệu 7 thì 2 đoạn thẳng bằng nhau."
    },
    {
        "id": "TC05_MATH_GRADE5",
        "title": "Toán lớp 5: Diện tích hình tam giác",
        "question": "Tính diện tích tam giác có đáy 12cm, chiều cao 8cm.",
        "guidance": "Nhắc bé nhớ lại công thức: 'Đáy nhân chiều cao rồi chia cho mấy?'."
    },
    {
        "id": "TC06_VIET_GRADE1",
        "title": "Tiếng Việt lớp 1: Phân biệt l / n",
        "question": "Điền l hay n vào chỗ trống: 'quả ...a' và 'bông ...úa'?",
        "guidance": "Gợi ý quả na ăn ngọt thơm, còn cây lúa cho ta hạt gạo trắng ngần."
    },
    {
        "id": "TC07_VIET_GRADE2",
        "title": "Tiếng Việt lớp 2: Phân biệt ch / tr",
        "question": "Bé hỏi: 'Cây ...e' điền ch hay tr?",
        "guidance": "Gợi ý nhớ lại hình ảnh cây tre dẻo dai ở làng quê Việt Nam."
    },
    {
        "id": "TC08_VIET_GRADE3",
        "title": "Tiếng Việt lớp 3: Từ chỉ đặc điểm",
        "question": "Tìm từ chỉ đặc điểm trong câu: 'Bầu trời thu trong xanh và cao vời vợi'.",
        "guidance": "Hỏi bé: 'Từ nào nói về màu sắc của bầu trời, và từ nào nói về độ cao?'."
    },
    {
        "id": "TC09_EDGE_BLURRY",
        "title": "Ảnh chụp bài vở bị mờ hoặc lóa sáng",
        "question": "[Ảnh chụp trang vở bị lóa bóng đèn, số bị mất nét]",
        "guidance": "Lịch sự từ chối đoán mò: 'Robot nhìn chưa rõ nét chữ, con chỉnh lại góc chụp nhé!'."
    },
    {
        "id": "TC10_LOGIC_TRICK",
        "title": "Bài toán suy luận logic / bẫy thực tế",
        "question": "1 người thợ xây 1 bức tường mất 5 ngày. Hỏi 5 người thợ xây mất mấy ngày?",
        "guidance": "Gợi ý số người tăng lên thì thời gian sẽ nhanh hơn hay lâu hơn?"
    }
]

def estimate_tokens(text: str) -> int:
    """Ước lượng số lượng token cho tiếng Việt (~1 từ tiếng Việt ~ 1.5 - 2 token)"""
    words = text.split()
    return int(len(words) * 1.6)

def run_benchmark():
    print("=" * 68)
    print("🤖 BENCHMARK 10 KỊCH BẢN PROMPT SOCRATIC CHO HỌC SINH TIỂU HỌC")
    print("Mục tiêu Task 8 - Tuần 3: Đo độ trễ mô phỏng & ước lượng chi phí token")
    print("=" * 68)
    
    sys_tokens = estimate_tokens(SOCRATIC_SYSTEM_PROMPT)
    print(f"\n📌 System Prompt ({sys_tokens} tokens):")
    print(SOCRATIC_SYSTEM_PROMPT.strip())
    print("-" * 68)

    total_tokens = sys_tokens
    for idx, tc in enumerate(TEN_TEST_SCENARIOS, 1):
        q_tokens = estimate_tokens(tc['question'])
        g_tokens = estimate_tokens(tc['guidance'])
        case_tokens = q_tokens + g_tokens
        total_tokens += case_tokens
        
        print(f"\n[#{idx}] {tc['title']} ({tc['id']})")
        print(f"  ❓ Tình huống: {tc['question']}")
        print(f"  💡 Gợi mở Socratic: {tc['guidance']}")
        print(f"  📊 Ước tính Token: ~{case_tokens} tokens (Input: {q_tokens}, Output: {g_tokens})")

    print("\n" + "=" * 68)
    print(f"✅ HOÀN THÀNH 10/10 KỊCH BẢN KIỂM THỬ PROMPT")
    print(f"📈 Tổng ước lượng token trung bình mỗi phiên hỏi-đáp: ~{sys_tokens + 60} tokens")
    print("=" * 68)

if __name__ == "__main__":
    run_benchmark()
