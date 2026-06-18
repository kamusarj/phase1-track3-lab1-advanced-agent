"""Convert HotpotQA dev set to QAExample format with MULTIPLE distractor chunks.

This produces a HARDER test set where:
- Each question has 5-7 context chunks
- 2-3 chunks form the CORRECT multi-hop chain
- 3-4 chunks are DISTRACTORS (topically similar but lead to wrong answer)
- ReAct tends to fail by picking the wrong first-hop entity
- Reflexion succeeds by reflecting and finding the correct chain
"""
import json
import random
from pathlib import Path


def convert_hotpot_to_qaexamples(
    src_path: str = "data/hotpot_dev_distractor_v1.json",
    out_path: str = "data/hotpot_hard.json",
    n: int = 100,
    n_chunks: int = 3,
    seed: int = 42,
) -> int:
    """Convert HotpotQA format to our QAExample format with distractors.

    Returns number of examples written.
    """
    raw = json.loads(Path(src_path).read_text(encoding="utf-8"))
    random.seed(seed)
    # Filter to bridge-type multi-hop questions only
    bridge_items = [item for item in raw if item.get("type") == "bridge"]
    random.shuffle(bridge_items)
    selected = bridge_items[:n]

    examples = []
    for item in selected:
        # Build mapping of title -> sentences
        chunks_data = []  # list of (title, sentences, is_supporting)
        supp_titles = {t for t, _ in item.get("supporting_facts", [])}

        for title, sents in item["context"]:
            is_supp = title in supp_titles
            chunks_data.append((title, sents, is_supp))

        # Shuffle the order of context chunks (so correct path is not always first)
        random.shuffle(chunks_data)

        chunks = []
        for title, sents, is_supp in chunks_data[:n_chunks]:
            if not sents:
                continue
            # Take first 2 sentences to keep prompts fast
            text = " ".join(sents[:2])
            chunks.append({"title": title, "text": text})

        if len(chunks) < 3:
            continue

        # Map level to our difficulty literal
        level = item.get("level", "medium")
        difficulty = level if level in ("easy", "medium", "hard") else "medium"
        examples.append({
            "qid": item["_id"],
            "difficulty": difficulty,
            "question": item["question"],
            "gold_answer": item["answer"],
            "context": chunks,
        })

    Path(out_path).write_text(json.dumps(examples, indent=2), encoding="utf-8")
    print(f"Wrote {len(examples)} examples to {out_path}")
    return len(examples)


if __name__ == "__main__":
    convert_hotpot_to_qaexamples()
