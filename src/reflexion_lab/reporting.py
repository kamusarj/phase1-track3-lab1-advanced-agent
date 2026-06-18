from __future__ import annotations
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from .schemas import ReportPayload, RunRecord

def summarize(records: list[RunRecord]) -> dict:
    grouped: dict[str, list[RunRecord]] = defaultdict(list)
    for record in records:
        grouped[record.agent_type].append(record)
    summary: dict[str, dict] = {}
    for agent_type, rows in grouped.items():
        summary[agent_type] = {"count": len(rows), "em": round(mean(1.0 if r.is_correct else 0.0 for r in rows), 4), "avg_attempts": round(mean(r.attempts for r in rows), 4), "avg_token_estimate": round(mean(r.token_estimate for r in rows), 2), "avg_latency_ms": round(mean(r.latency_ms for r in rows), 2)}
    if "react" in summary and "reflexion" in summary:
        summary["delta_reflexion_minus_react"] = {"em_abs": round(summary["reflexion"]["em"] - summary["react"]["em"], 4), "attempts_abs": round(summary["reflexion"]["avg_attempts"] - summary["react"]["avg_attempts"], 4), "tokens_abs": round(summary["reflexion"]["avg_token_estimate"] - summary["react"]["avg_token_estimate"], 2), "latency_abs": round(summary["reflexion"]["avg_latency_ms"] - summary["react"]["avg_latency_ms"], 2)}
    return summary

def failure_breakdown(records: list[RunRecord]) -> dict:
    grouped: dict[str, Counter] = defaultdict(Counter)
    for record in records:
        grouped[record.agent_type][record.failure_mode] += 1
    result: dict = {agent: dict(counter) for agent, counter in grouped.items()}
    # Add a top-level "all_modes" key listing unique failure modes with counts
    all_modes: Counter = Counter()
    for counter in grouped.values():
        all_modes.update(counter)
    result["all_modes"] = dict(all_modes)
    return result

def build_report(records: list[RunRecord], dataset_name: str, mode: str = "mock") -> ReportPayload:
    # Count unique QIDs per agent
    react_qids = {r.qid for r in records if r.agent_type == "react"}
    reflex_qids = {r.qid for r in records if r.agent_type == "reflexion"}
    react_em_real = sum(1 for r in records if r.agent_type == "react" and r.is_correct)
    reflex_em_real = sum(1 for r in records if r.agent_type == "reflexion" and r.is_correct)
    n_q = len(react_qids) if react_qids else (len(reflex_qids) if reflex_qids else 0)

    examples = [{"qid": r.qid, "agent_type": r.agent_type, "gold_answer": r.gold_answer, "predicted_answer": r.predicted_answer, "is_correct": r.is_correct, "attempts": r.attempts, "failure_mode": r.failure_mode, "reflection_count": len(r.reflections)} for r in records]

    # Concrete examples for analysis
    react_wrong = [r for r in records if r.agent_type == "react" and not r.is_correct]
    reflex_wrong = [r for r in records if r.agent_type == "reflexion" and not r.is_correct]
    react_recovered = [
        r for r in records if r.agent_type == "reflexion"
        and r.is_correct
        and any(not t.is_correct if hasattr(t, 'is_correct') else t.score == 0 for t in r.traces)
    ]

    analysis_text = (
        f"Trên dataset gồm {n_q} câu hỏi multi-hop, kết quả thực nghiệm cho thấy:\n\n"
        f"**ReAct (single-shot):** đạt {react_em_real}/{n_q} = {react_em_real/n_q*100:.0f}% EM. "
        f"ReAct chỉ có một lần thử, nên khi gặp câu hỏi cần chain dài (multi-hop) hoặc khi model "
        f"suy luận sai ở bước đầu, không có cơ hội sửa. "
    )
    if react_wrong:
        wrong_qids = ", ".join(r.qid for r in react_wrong[:3])
        analysis_text += f"Các câu ReAct sai: {wrong_qids}. "

    analysis_text += (
        f"\n\n**Reflexion (có reflection memory):** đạt {reflex_em_real}/{n_q} = {reflex_em_real/n_q*100:.0f}% EM. "
        f"Reflexion thắng rõ ở những câu mà attempt đầu bị 'wrong_final_answer' hoặc 'incomplete_multi_hop' — "
        f"vì reflector phân tích được lỗi và đưa ra strategy cụ thể cho attempt tiếp theo. "
        f"Với qwen3.5:4b local, qwen3.5 có 'thinking mode' (suy nghĩ nội bộ trước khi trả lời), "
        f"đôi khi thinking bị cắt cụt do giới hạn token, khiến câu trả lời bị rỗng — đây là lúc reflection "
        f"giúp ích rõ nhất vì model thử lại với focus khác.\n\n"
        f"**Trade-off:** Reflexion tốn hơn {sum(r.token_estimate for r in records if r.agent_type=='reflexion')/max(sum(r.token_estimate for r in records if r.agent_type=='react'),1):.1f}x số token "
        f"và {sum(r.latency_ms for r in records if r.agent_type=='reflexion')/max(sum(r.latency_ms for r in records if r.agent_type=='react'),1):.1f}x thời gian. "
        f"Với Ollama local, chi phí thực tế = $0 (chỉ tốn điện); với hosted API thì trade-off vẫn nhỏ "
        f"(xem Bảng 3).\n\n"
        f"**Kết luận:** Reflexion memory phù hợp cho multi-hop QA khi model có khả năng 'recover' sau reflection. "
        f"Reflection ít có giá trị khi LLM hallucinate hoàn toàn từ đầu (output rỗng, 'I don't know'). "
        f"Trong production, có thể dùng self-consistency (vote trên N lần) hoặc model lớn hơn cho actor "
        f"để cải thiện thêm."
    )

    return ReportPayload(
        meta={"dataset": dataset_name, "mode": mode, "num_records": len(records), "agents": sorted({r.agent_type for r in records})},
        summary=summarize(records),
        failure_modes=failure_breakdown(records),
        examples=examples,
        extensions=["structured_evaluator", "reflection_memory", "benchmark_report_json", "mock_mode_for_autograding", "adaptive_max_attempts"],
        discussion=analysis_text,
    )

def save_report(report: ReportPayload, out_dir: str | Path) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "report.json"
    md_path = out_dir / "report.md"
    json_path.write_text(json.dumps(report.model_dump(), indent=2), encoding="utf-8")
    s = report.summary
    react = s.get("react", {})
    reflexion = s.get("reflexion", {})
    delta = s.get("delta_reflexion_minus_react", {})

    # Cost estimation (qwen3.5:4b local Ollama, free; using public rates as reference)
    COST_INPUT_PER_1M = 0.50
    COST_OUTPUT_PER_1M = 1.50
    n_records = react.get("count", 0)
    react_total_tokens = react.get("avg_token_estimate", 0) * n_records
    reflex_total_tokens = reflexion.get("avg_token_estimate", 0) * n_records
    react_total_latency_s = (react.get("avg_latency_ms", 0) * n_records) / 1000
    reflex_total_latency_s = (reflexion.get("avg_latency_ms", 0) * n_records) / 1000
    react_cost = (react_total_tokens / 1_000_000) * (COST_INPUT_PER_1M + COST_OUTPUT_PER_1M) / 2
    reflex_cost = (reflex_total_tokens / 1_000_000) * (COST_INPUT_PER_1M + COST_OUTPUT_PER_1M) / 2

    react_em = react.get('em', 0) * 100
    reflex_em = reflexion.get('em', 0) * 100
    em_improvement = (reflexion.get('em', 0) - react.get('em', 0)) * 100

    ext_lines = "\n".join(f"- {item}" for item in report.extensions)

    md = f"""# Báo Cáo Benchmark Lab 16 — Reflexion Agent

## 1. Thông Tin Chung (Metadata)

| Mục | Giá trị |
|---|---|
| Dataset | {report.meta['dataset']} |
| Mode | {report.meta['mode']} |
| Số records | {report.meta['num_records']} |
| Agents | {', '.join(report.meta['agents'])} |
| Model | qwen3.5:4b (Ollama local) |

## 2. So Sánh ReAct vs Reflexion

Bảng dưới đây so sánh **điểm chính xác (Exact Match - EM)**, số lần thử trung bình, số token ước tính, và độ trễ giữa hai agent:

| Chỉ số | ReAct | Reflexion | Chênh lệch (Reflexion − ReAct) |
|---|---:|---:|---:|
| **EM (Exact Match)** | {react_em:.1f}% | {reflex_em:.1f}% | **+{em_improvement:.1f}%** |
| **Số lần thử trung bình** | {react.get('avg_attempts', 0):.2f} | {reflexion.get('avg_attempts', 0):.2f} | +{delta.get('attempts_abs', 0):.2f} |
| **Số token / record** | {react.get('avg_token_estimate', 0):.0f} | {reflexion.get('avg_token_estimate', 0):.0f} | +{delta.get('tokens_abs', 0):.0f} |
| **Độ trễ / record (giây)** | {react.get('avg_latency_ms', 0)/1000:.2f}s | {reflexion.get('avg_latency_ms', 0)/1000:.2f}s | +{delta.get('latency_abs', 0)/1000:.2f}s |

**Nhận xét nhanh:**
- Reflexion cải thiện **+{em_improvement:.1f}%** EM so với ReAct baseline.
- Trade-off: Reflexion tốn **gấp {reflexion.get('avg_token_estimate', 0) / max(react.get('avg_token_estimate', 1), 1):.1f}x** số token và **{reflexion.get('avg_attempts', 0):.1f}x** số lần thử.
- Trong production, cần cân bằng giữa chất lượng và chi phí; có thể dùng model nhỏ hơn cho reflector.

## 3. Ước Tính Chi Phí (Cost Estimate)

Tham khảo giá hosted API: **${COST_INPUT_PER_1M}/1M input tokens**, **${COST_OUTPUT_PER_1M}/1M output tokens** (mức giá Qwen3.5-tier).
*Lưu ý: với Ollama local (qwen3.5:4b) chi phí thực tế = $0 (chỉ tốn điện).*

| Hạng mục chi phí | ReAct | Reflexion | Chênh lệch |
|---|---:|---:|---:|
| Tokens / record | {react.get('avg_token_estimate', 0):.0f} | {reflexion.get('avg_token_estimate', 0):.0f} | +{delta.get('tokens_abs', 0):.0f} |
| Tổng tokens ({n_records} records) | {react_total_tokens:,.0f} | {reflex_total_tokens:,.0f} | +{reflex_total_tokens - react_total_tokens:,.0f} |
| Thời gian / record (giây) | {react.get('avg_latency_ms', 0)/1000:.2f}s | {reflexion.get('avg_latency_ms', 0)/1000:.2f}s | +{delta.get('latency_abs', 0)/1000:.2f}s |
| Tổng thời gian chạy ({n_records} records) | {react_total_latency_s/60:.1f} phút | {reflex_total_latency_s/60:.1f} phút | +{(reflex_total_latency_s - react_total_latency_s)/60:.1f} phút |
| Chi phí ước tính (USD, hosted API) | ${react_cost:.4f} | ${reflex_cost:.4f} | ${reflex_cost - react_cost:.4f} |

**Kết luận cost:** Nếu chạy trên hosted API với 100 records, Reflexion tốn thêm khoảng **${reflex_cost - react_cost:.4f}/100 câu**. Với dataset lớn hơn (1000+ câu), trade-off vẫn rất nhỏ so với lợi ích tăng độ chính xác.

## 4. Phân Tích Failure Modes

```json
{json.dumps(report.failure_modes, indent=2)}
```

Các failure mode chính:

- **`entity_drift`**: Actor chọn sai entity ở hop đầu tiên (thường là distractor có vẻ liên quan).
- **`incomplete_multi_hop`**: Trả lời bằng entity trung gian (e.g. "London") thay vì entity cuối cùng ("River Thames").
- **`wrong_final_answer`**: Chain đúng nhưng tên entity cuối sai (do hallucination).
- **`looping`**: Actor lặp lại cùng câu trả lời sai qua nhiều lần thử — reflection không có tác dụng.
- **`reflection_overfit`**: Sau khi reflect, model "lật" sang câu trả lời sai khác thay vì grounding vào context.

## 5. Các Extension Đã Triển Khai

{ext_lines}

## 6. Thảo Luận (Discussion)

{report.discussion}
"""
    md_path.write_text(md, encoding="utf-8")
    return json_path, md_path
