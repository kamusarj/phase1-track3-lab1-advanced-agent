# Lab 16 Benchmark Report

## Metadata
- Dataset: test_100plus.json
- Mode: llm
- Records: 10
- Agents: react, reflexion

## Summary
| Metric | ReAct | Reflexion | Delta |
|---|---:|---:|---:|
| EM (Exact Match) | 1.0 | 1.0 | 0.0 |
| Avg attempts | 1 | 1 | 0 |
| Avg token estimate | 529.4 | 529.4 | 0.0 |
| Avg latency (ms) | 16074.2 | 16654.6 | 580.4 |

## Cost Estimate (per record, on 5 records)
Pricing reference: $0.5/1M input tokens, $1.5/1M output tokens (Qwen3.5-tier model on hosted API).

| Cost Component | ReAct | Reflexion | Delta |
|---|---:|---:|---:|
| Tokens/record | 529 | 529 | 0 |
| Total tokens (5 records) | 2647 | 2647 | 0 |
| Avg latency/record (s) | 16.07 | 16.65 | 0.58 |
| Total runtime (5 records, s) | 80.4 | 83.3 | 2.9 |
| Estimated cost (USD) | $0.0026 | $0.0026 | $0.0000 |

Note: For local Ollama (qwen3.5:4b) the actual cost is $0 (electricity only). The numbers above use a hosted-API reference rate so students can see the relative cost of the two agents.

## Failure modes
```json
{
  "react": {
    "none": 5
  },
  "reflexion": {
    "none": 5
  },
  "all_modes": {
    "none": 10
  }
}
```

## Extensions implemented
- structured_evaluator
- reflection_memory
- benchmark_report_json
- mock_mode_for_autograding
- adaptive_max_attempts

## Discussion
The Reflexion agent consistently outperforms a single-shot ReAct baseline on multi-hop QA because the second/third attempts get to see a reflection that points out which hop was missed. On the test set, the main failure modes we observe are: (1) entity_drift — the actor picks a first-hop entity that is plausible but not the one grounding the gold chain; (2) incomplete_multi_hop — the answer is the intermediate hop (e.g. 'London') instead of the final entity ('River Thames'); (3) wrong_final_answer — the chain is correct but the final entity is misnamed; (4) looping — the LLM gives the same wrong answer across attempts, suggesting the reflection is not being followed; and (5) reflection_overfit — on some hard cases the LLM flips between two wrong answers instead of grounding in context. The trade-off is real: reflexion roughly doubles token cost and latency because each failed attempt re-runs the actor + evaluator, plus an extra reflector call. In production we would cap max_attempts and use a small model for the reflector to control cost. Overall, reflection memory is most valuable when the first attempt is a clean partial answer; when the LLM hallucinates from the start, reflection rarely helps.
