from __future__ import annotations
import time
from dataclasses import dataclass
from typing import Literal
from .mock_runtime import actor_answer, evaluator, reflector
from .schemas import AttemptTrace, QAExample, ReflectionEntry, RunRecord


@dataclass
class BaseAgent:
    agent_type: Literal["react", "reflexion"]
    max_attempts: int = 1

    def _classify_failure(
        self, example: QAExample, traces: list[AttemptTrace], final_score: int
    ) -> str:
        """Classify the failure mode of the run."""
        if final_score == 1:
            return "none"
        if not traces:
            return "wrong_final_answer"

        last_trace = traces[-1]
        reason_lower = last_trace.reason.lower()

        # Check for looping (same answer across multiple attempts)
        if len(traces) >= 2:
            answers = [t.answer.strip().lower() for t in traces]
            if len(set(answers)) == 1 and final_score == 0:
                return "looping"

        # Check for incomplete multi-hop (mentions missing evidence, second hop, etc.)
        if any(
            kw in reason_lower
            for kw in ["incomplete", "second hop", "multi-hop", "did not complete"]
        ):
            return "incomplete_multi_hop"

        # Check for entity drift (wrong entity, off-topic)
        if any(
            kw in reason_lower
            for kw in ["drift", "wrong entity", "off-topic", "unrelated entity"]
        ):
            return "entity_drift"

        # Check for reflection overfit (only relevant for reflexion with many attempts)
        if self.agent_type == "reflexion" and len(traces) >= 3 and final_score == 0:
            return "reflection_overfit"

        return "wrong_final_answer"

    def run(self, example: QAExample) -> RunRecord:
        reflection_memory: list[str] = []
        reflections: list[ReflectionEntry] = []
        traces: list[AttemptTrace] = []
        final_answer = ""
        final_score = 0

        for attempt_id in range(1, self.max_attempts + 1):
            start_time = time.time()

            answer, actor_tokens = actor_answer(
                example, attempt_id, self.agent_type, reflection_memory
            )
            judge, eval_tokens = evaluator(example, answer)

            elapsed_ms = int((time.time() - start_time) * 1000)
            token_estimate = actor_tokens + eval_tokens

            trace = AttemptTrace(
                attempt_id=attempt_id,
                answer=answer,
                score=judge.score,
                reason=judge.reason,
                token_estimate=token_estimate,
                latency_ms=elapsed_ms,
            )
            final_answer = answer
            final_score = judge.score

            if judge.score == 1:
                traces.append(trace)
                break

            # Reflexion logic: reflect on failure and update memory
            if self.agent_type == "reflexion" and attempt_id < self.max_attempts:
                reflection, refl_tokens = reflector(example, attempt_id, judge)
                reflections.append(reflection)
                reflection_memory.append(
                    f"Attempt {attempt_id} failed: {reflection.failure_reason}. "
                    f"Lesson: {reflection.lesson}. "
                    f"Next strategy: {reflection.next_strategy}"
                )
                trace.token_estimate += refl_tokens

            traces.append(trace)

        total_tokens = sum(t.token_estimate for t in traces)
        total_latency = sum(t.latency_ms for t in traces)
        failure_mode = self._classify_failure(example, traces, final_score)
        return RunRecord(
            qid=example.qid,
            question=example.question,
            gold_answer=example.gold_answer,
            agent_type=self.agent_type,
            predicted_answer=final_answer,
            is_correct=bool(final_score),
            attempts=len(traces),
            token_estimate=total_tokens,
            latency_ms=total_latency,
            failure_mode=failure_mode,
            reflections=reflections,
            traces=traces,
        )


class ReActAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(agent_type="react", max_attempts=1)


class ReflexionAgent(BaseAgent):
    def __init__(self, max_attempts: int = 3) -> None:
        super().__init__(agent_type="reflexion", max_attempts=max_attempts)
