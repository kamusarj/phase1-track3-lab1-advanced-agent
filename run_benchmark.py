from __future__ import annotations
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import typer
from rich import print
from src.reflexion_lab.agents import ReActAgent, ReflexionAgent
from src.reflexion_lab.reporting import build_report, save_report
from src.reflexion_lab.utils import load_dataset, save_jsonl
app = typer.Typer(add_completion=False)

def _run_parallel(agent, examples, max_workers: int = 8):
    def _one(ex):
        return agent.run(ex)
    results = [None] * len(examples)
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(_one, ex): i for i, ex in enumerate(examples)}
        done = 0
        for fut in as_completed(futures):
            i = futures[fut]
            results[i] = fut.result()
            done += 1
            if done % 10 == 0 or done == len(examples):
                print(f"  ... {done}/{len(examples)} done")
    return results

@app.command()
def main(dataset: str = "data/hotpot_mini.json", out_dir: str = "outputs/sample_run", reflexion_attempts: int = 2, limit: int = 0, workers: int = 8) -> None:
    examples = load_dataset(dataset)
    if limit and limit > 0:
        examples = examples[:limit]
    print(f"[cyan]Loaded {len(examples)} examples from {dataset}[/cyan]")
    react = ReActAgent()
    reflexion = ReflexionAgent(max_attempts=reflexion_attempts)

    print(f"[cyan]Running ReAct agent (workers={workers})...[/cyan]")
    react_records = _run_parallel(react, examples, max_workers=workers)
    print(f"[green]ReAct done: {sum(r.is_correct for r in react_records)}/{len(react_records)} correct[/green]")

    print(f"[cyan]Running Reflexion agent (max_attempts={reflexion_attempts}, workers={workers})...[/cyan]")
    reflexion_records = _run_parallel(reflexion, examples, max_workers=workers)
    print(f"[green]Reflexion done: {sum(r.is_correct for r in reflexion_records)}/{len(reflexion_records)} correct[/green]")

    all_records = react_records + reflexion_records
    out_path = Path(out_dir)
    save_jsonl(out_path / "react_runs.jsonl", react_records)
    save_jsonl(out_path / "reflexion_runs.jsonl", reflexion_records)
    report = build_report(all_records, dataset_name=Path(dataset).name, mode="llm")
    json_path, md_path = save_report(report, out_path)
    print(f"[green]Saved[/green] {json_path}")
    print(f"[green]Saved[/green] {md_path}")
    print(json.dumps(report.summary, indent=2))

if __name__ == "__main__":
    app()
