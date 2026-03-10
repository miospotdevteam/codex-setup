#!/usr/bin/env python3
"""Run trigger evaluation for a skill description.

This Codex port uses an OpenAI model to approximate whether a skill should
trigger for a given query. It does not measure the exact Codex runtime.
"""

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from openai import OpenAI

from scripts.utils import extract_json_object, parse_skill_md


SYSTEM_PROMPT = """You are evaluating whether a Codex skill should trigger.

You will receive:
- a skill name
- a skill description
- a user query

Return JSON with:
{
  "triggered": true or false,
  "reason": "one short sentence"
}

Rules:
- Trigger only when the skill would materially help with a specialized or
  multi-step task beyond Codex's default capability.
- Do not trigger just because of a loose keyword overlap.
- Be conservative about trivial requests.
- Respond with JSON only.
"""


def find_project_root() -> Path:
    """Find a reasonable project root for output placement."""
    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / ".git").is_dir() or (parent / "AGENTS.md").is_file() or (parent / "README.md").is_file():
            return parent
    return current


def run_single_query(
    query: str,
    skill_name: str,
    skill_description: str,
    timeout: int,
    project_root: str,
    model: str | None = None,
) -> bool:
    """Run a single approximate trigger evaluation."""
    del timeout
    del project_root

    client = OpenAI()
    response = client.responses.create(
        model=model or "gpt-5-mini",
        max_output_tokens=200,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Skill name: {skill_name}\n"
                    f"Skill description: {skill_description}\n"
                    f"User query: {query}\n"
                ),
            },
        ],
    )
    parsed = extract_json_object(response.output_text)
    return bool(parsed.get("triggered", False))


def run_eval(
    eval_set: list[dict],
    skill_name: str,
    description: str,
    num_workers: int,
    timeout: int,
    project_root: Path,
    runs_per_query: int = 1,
    trigger_threshold: float = 0.5,
    model: str | None = None,
) -> dict:
    """Run the full eval set and return results."""
    del timeout

    results = []

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        future_to_info = {}
        for item in eval_set:
            for run_idx in range(runs_per_query):
                future = executor.submit(
                    run_single_query,
                    item["query"],
                    skill_name,
                    description,
                    timeout,
                    str(project_root),
                    model,
                )
                future_to_info[future] = (item, run_idx)

        query_triggers: dict[str, list[bool]] = {}
        query_items: dict[str, dict] = {}
        for future in as_completed(future_to_info):
            item, _ = future_to_info[future]
            query = item["query"]
            query_items[query] = item
            query_triggers.setdefault(query, [])
            try:
                query_triggers[query].append(future.result())
            except Exception as exc:
                print(f"Warning: query failed: {exc}", file=sys.stderr)
                query_triggers[query].append(False)

    for query, triggers in query_triggers.items():
        item = query_items[query]
        trigger_rate = sum(triggers) / len(triggers)
        should_trigger = item["should_trigger"]
        did_pass = (
            trigger_rate >= trigger_threshold if should_trigger else trigger_rate < trigger_threshold
        )
        results.append(
            {
                "query": query,
                "should_trigger": should_trigger,
                "trigger_rate": trigger_rate,
                "triggers": sum(triggers),
                "runs": len(triggers),
                "pass": did_pass,
            }
        )

    passed = sum(1 for result in results if result["pass"])
    total = len(results)

    return {
        "skill_name": skill_name,
        "description": description,
        "results": results,
        "summary": {
            "total": total,
            "passed": passed,
            "failed": total - passed,
        },
        "mode": "approximate-openai-trigger-eval",
    }


def main():
    parser = argparse.ArgumentParser(description="Run approximate trigger evaluation for a Codex skill description")
    parser.add_argument("--eval-set", required=True, help="Path to eval set JSON file")
    parser.add_argument("--skill-path", required=True, help="Path to skill directory")
    parser.add_argument("--description", default=None, help="Override description instead of SKILL.md frontmatter")
    parser.add_argument("--num-workers", type=int, default=10, help="Number of parallel workers")
    parser.add_argument("--timeout", type=int, default=30, help="Unused compatibility flag")
    parser.add_argument("--runs-per-query", type=int, default=3, help="Number of runs per query")
    parser.add_argument("--trigger-threshold", type=float, default=0.5, help="Trigger rate threshold")
    parser.add_argument("--model", default=None, help="OpenAI model to use (default: gpt-5-mini)")
    args = parser.parse_args()

    eval_set = json.loads(Path(args.eval_set).read_text())
    skill_path = Path(args.skill_path)

    if not (skill_path / "SKILL.md").exists():
        print(f"Error: No SKILL.md found at {skill_path}", file=sys.stderr)
        sys.exit(1)

    name, original_description, _ = parse_skill_md(skill_path)
    description = args.description or original_description

    output = run_eval(
        eval_set=eval_set,
        skill_name=name,
        description=description,
        num_workers=args.num_workers,
        timeout=args.timeout,
        project_root=find_project_root(),
        runs_per_query=args.runs_per_query,
        trigger_threshold=args.trigger_threshold,
        model=args.model,
    )
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
