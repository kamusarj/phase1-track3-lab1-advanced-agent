"""Tests for the reflexion_lab agents and runtime."""
import os
from src.reflexion_lab.schemas import JudgeResult, ReflectionEntry, QAExample, ContextChunk
from src.reflexion_lab.utils import normalize_answer


def test_judge_result_serialization():
    jr = JudgeResult(score=1, reason="ok", missing_evidence=[], spurious_claims=[])
    data = jr.model_dump()
    assert data["score"] == 1
    assert data["reason"] == "ok"


def test_reflection_entry_serialization():
    re = ReflectionEntry(
        attempt_id=1,
        failure_reason="wrong",
        lesson="learn",
        next_strategy="try again",
    )
    data = re.model_dump()
    assert data["attempt_id"] == 1
    assert data["next_strategy"] == "try again"


def test_qa_example_load():
    ex = QAExample(
        qid="q1",
        difficulty="easy",
        question="What?",
        gold_answer="X",
        context=[ContextChunk(title="T", text="t")],
    )
    assert ex.qid == "q1"


def test_normalize():
    assert normalize_answer("The River Thames!") == "the river thames"


def test_failure_classification(monkeypatch):
    from src.reflexion_lab.agents import ReActAgent, ReflexionAgent
    from src.reflexion_lab.schemas import AttemptTrace

    agent = ReActAgent()
    # Empty case
    assert agent._classify_failure(None, [], 0) == "wrong_final_answer"
    # Looping case
    traces = [
        AttemptTrace(attempt_id=1, answer="A", score=0, reason="wrong"),
        AttemptTrace(attempt_id=2, answer="A", score=0, reason="wrong"),
    ]
    assert agent._classify_failure(None, traces, 0) == "looping"
    # Success case
    traces = [AttemptTrace(attempt_id=1, answer="X", score=1, reason="ok")]
    assert agent._classify_failure(None, traces, 1) == "none"


def test_agent_imports():
    """Make sure we can import the agents without error."""
    from src.reflexion_lab.agents import ReActAgent, ReflexionAgent
    from src.reflexion_lab.mock_runtime import actor_answer, evaluator, reflector
    assert ReActAgent is not None
    assert ReflexionAgent is not None
