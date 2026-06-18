# Báo Cáo Benchmark Lab 16 — Reflexion Agent

## 1. Thông Tin Chung (Metadata)

| Mục | Giá trị |
|---|---|
| Dataset | hotpot_golden.json |
| Mode | llm |
| Số records | 40 |
| Agents | react, reflexion |
| Model | qwen3.5:4b (Ollama local) |

## 2. So Sánh ReAct vs Reflexion

Bảng dưới đây so sánh **điểm chính xác (Exact Match - EM)**, số lần thử trung bình, số token ước tính, và độ trễ giữa hai agent:

| Chỉ số | ReAct | Reflexion | Chênh lệch (Reflexion − ReAct) |
|---|---:|---:|---:|
| **EM (Exact Match)** | 85.0% | 100.0% | **+15.0%** |
| **Số lần thử trung bình** | 1.00 | 1.15 | +0.15 |
| **Số token / record** | 870 | 1187 | +317 |
| **Độ trễ / record (giây)** | 25.15s | 29.44s | +4.28s |

**Nhận xét nhanh:**
- Reflexion cải thiện **+15.0%** EM so với ReAct baseline.
- Trade-off: Reflexion tốn **gấp 1.4x** số token và **1.1x** số lần thử.
- Trong production, cần cân bằng giữa chất lượng và chi phí; có thể dùng model nhỏ hơn cho reflector.

## 3. Ước Tính Chi Phí (Cost Estimate)

Tham khảo giá hosted API: **$0.5/1M input tokens**, **$1.5/1M output tokens** (mức giá Qwen3.5-tier).
*Lưu ý: với Ollama local (qwen3.5:4b) chi phí thực tế = $0 (chỉ tốn điện).*

| Hạng mục chi phí | ReAct | Reflexion | Chênh lệch |
|---|---:|---:|---:|
| Tokens / record | 870 | 1187 | +317 |
| Tổng tokens (20 records) | 17,410 | 23,744 | +6,334 |
| Thời gian / record (giây) | 25.15s | 29.44s | +4.28s |
| Tổng thời gian chạy (20 records) | 8.4 phút | 9.8 phút | +1.4 phút |
| Chi phí ước tính (USD, hosted API) | $0.0174 | $0.0237 | $0.0063 |

**Kết luận cost:** Nếu chạy trên hosted API với 100 records, Reflexion tốn thêm khoảng **$0.0063/100 câu**. Với dataset lớn hơn (1000+ câu), trade-off vẫn rất nhỏ so với lợi ích tăng độ chính xác.

## 4. Phân Tích Failure Modes

```json
{
  "react": {
    "none": 17,
    "wrong_final_answer": 3
  },
  "reflexion": {
    "none": 20
  },
  "all_modes": {
    "none": 37,
    "wrong_final_answer": 3
  }
}
```

Các failure mode chính:

- **`entity_drift`**: Actor chọn sai entity ở hop đầu tiên (thường là distractor có vẻ liên quan).
- **`incomplete_multi_hop`**: Trả lời bằng entity trung gian (e.g. "London") thay vì entity cuối cùng ("River Thames").
- **`wrong_final_answer`**: Chain đúng nhưng tên entity cuối sai (do hallucination).
- **`looping`**: Actor lặp lại cùng câu trả lời sai qua nhiều lần thử — reflection không có tác dụng.
- **`reflection_overfit`**: Sau khi reflect, model "lật" sang câu trả lời sai khác thay vì grounding vào context.

## 5. Các Extension Đã Triển Khai

- structured_evaluator
- reflection_memory
- benchmark_report_json
- mock_mode_for_autograding
- adaptive_max_attempts

## 6. Thảo Luận (Discussion)

Trên dataset gồm 20 câu hỏi multi-hop, kết quả thực nghiệm cho thấy:

**ReAct (single-shot):** đạt 17/20 = 85% EM. ReAct chỉ có một lần thử, nên khi gặp câu hỏi cần chain dài (multi-hop) hoặc khi model suy luận sai ở bước đầu, không có cơ hội sửa. Các câu ReAct sai: gold5, gold6, gold7. 

**Reflexion (có reflection memory):** đạt 20/20 = 100% EM. Reflexion thắng rõ ở những câu mà attempt đầu bị 'wrong_final_answer' hoặc 'incomplete_multi_hop' — vì reflector phân tích được lỗi và đưa ra strategy cụ thể cho attempt tiếp theo. Với qwen3.5:4b local, qwen3.5 có 'thinking mode' (suy nghĩ nội bộ trước khi trả lời), đôi khi thinking bị cắt cụt do giới hạn token, khiến câu trả lời bị rỗng — đây là lúc reflection giúp ích rõ nhất vì model thử lại với focus khác.

**Trade-off:** Reflexion tốn hơn 1.4x số token và 1.2x thời gian. Với Ollama local, chi phí thực tế = $0 (chỉ tốn điện); với hosted API thì trade-off vẫn nhỏ (xem Bảng 3).

**Kết luận:** Reflexion memory phù hợp cho multi-hop QA khi model có khả năng 'recover' sau reflection. Reflection ít có giá trị khi LLM hallucinate hoàn toàn từ đầu (output rỗng, 'I don't know'). Trong production, có thể dùng self-consistency (vote trên N lần) hoặc model lớn hơn cho actor để cải thiện thêm.
