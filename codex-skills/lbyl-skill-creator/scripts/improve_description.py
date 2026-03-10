#!/usr/bin/env python3
"""Improve a skill description based on eval results using OpenAI."""

import argparse
import json
import re
import sys
from pathlib import Path

from openai import OpenAI

from scripts.utils import parse_skill_md


def call_text_model(client: OpenAI, model: str, prompt: str) -> str:
    response = client.responses.create(
        model=model,
        max_output_tokens=1200,
        input=[{"role": "user", "content": prompt}],
    )
    return response.output_text


def improve_description(
    skill_name: str,
    skill_content: str,
    current_description: str,
    eval_results: dict,
    history: list[dict],
    model: str,
    test_results: dict | None = None,
    log_dir: Path | None = None,
    iteration: int | None = None,
) -> str:
    """Call an OpenAI model to improve the description based on eval results."""
    client = OpenAI()
    failed_triggers = [
        result for result in eval_results["results"]
        if result["should_trigger"] and not result["pass"]
    ]
    false_triggers = [
        result for result in eval_results["results"]
        if not result["should_trigger"] and not result["pass"]
    ]

    train_score = f"{eval_results['summary']['passed']}/{eval_results['summary']['total']}"
    scores_summary = f"Train: {train_score}"
    if test_results:
        test_score = f"{test_results['summary']['passed']}/{test_results['summary']['total']}"
        scores_summary = f"{scores_summary}, Test: {test_score}"

    prompt = f"""You are optimizing a Codex skill description for a skill called "{skill_name}".

The skill description is the metadata users and the runtime see before reading
the full SKILL.md. Your job is to improve the description so it triggers for
relevant requests and stays quiet for irrelevant ones.

Current description:
<current_description>
{current_description}
</current_description>

Current scores: {scores_summary}
"""

    if failed_triggers:
        prompt += "\nFAILED TO TRIGGER:\n"
        for result in failed_triggers:
            prompt += f'- "{result["query"]}" ({result["triggers"]}/{result["runs"]})\n'

    if false_triggers:
        prompt += "\nFALSE TRIGGERS:\n"
        for result in false_triggers:
            prompt += f'- "{result["query"]}" ({result["triggers"]}/{result["runs"]})\n'

    if history:
        prompt += "\nPREVIOUS ATTEMPTS:\n"
        for item in history:
            train_s = f"{item.get('train_passed', item.get('passed', 0))}/{item.get('train_total', item.get('total', 0))}"
            test_s = (
                f"{item.get('test_passed')}/{item.get('test_total')}"
                if item.get("test_passed") is not None
                else None
            )
            score_str = f"train={train_s}" + (f", test={test_s}" if test_s else "")
            prompt += f'- {score_str}: "{item["description"]}"\n'

    prompt += f"""

Skill content for context:
<skill_content>
{skill_content}
</skill_content>

Write a better description. Constraints:
- Keep it under 1024 characters
- Make it concrete about when to use the skill
- Include negative boundaries when helpful
- Avoid keyword stuffing
- Optimize for Codex users, not Claude-specific wording

Respond with only the new description wrapped in <new_description> tags.
"""

    text = call_text_model(client, model, prompt)
    match = re.search(r"<new_description>(.*?)</new_description>", text, re.DOTALL)
    description = match.group(1).strip().strip('"') if match else text.strip().strip('"')

    transcript: dict = {
        "iteration": iteration,
        "prompt": prompt,
        "response": text,
        "parsed_description": description,
        "char_count": len(description),
        "over_limit": len(description) > 1024,
    }

    if len(description) > 1024:
        shorten_prompt = (
            f"Rewrite this skill description to be under 1024 characters while preserving "
            f"the important trigger intent.\n\n<description>{description}</description>\n"
            "Respond with only the shortened description in <new_description> tags."
        )
        shorten_text = call_text_model(client, model, shorten_prompt)
        match = re.search(r"<new_description>(.*?)</new_description>", shorten_text, re.DOTALL)
        description = match.group(1).strip().strip('"') if match else shorten_text.strip().strip('"')
        transcript["rewrite_prompt"] = shorten_prompt
        transcript["rewrite_response"] = shorten_text
        transcript["rewrite_char_count"] = len(description)

    transcript["final_description"] = description

    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"improve_iter_{iteration or 'unknown'}.json"
        log_file.write_text(json.dumps(transcript, indent=2))

    return description


def main():
    parser = argparse.ArgumentParser(description="Improve a skill description based on eval results")
    parser.add_argument("--eval-results", required=True, help="Path to eval results JSON")
    parser.add_argument("--skill-path", required=True, help="Path to skill directory")
    parser.add_argument("--history", default=None, help="Path to history JSON")
    parser.add_argument("--model", required=True, help="OpenAI model for improvement")
    parser.add_argument("--verbose", action="store_true", help="Print progress to stderr")
    args = parser.parse_args()

    skill_path = Path(args.skill_path)
    if not (skill_path / "SKILL.md").exists():
        print(f"Error: No SKILL.md found at {skill_path}", file=sys.stderr)
        sys.exit(1)

    eval_results = json.loads(Path(args.eval_results).read_text())
    history = json.loads(Path(args.history).read_text()) if args.history else []

    name, _, content = parse_skill_md(skill_path)
    current_description = eval_results["description"]

    if args.verbose:
        print(f"Current: {current_description}", file=sys.stderr)

    new_description = improve_description(
        skill_name=name,
        skill_content=content,
        current_description=current_description,
        eval_results=eval_results,
        history=history,
        model=args.model,
    )

    output = {
        "description": new_description,
        "history": history + [{
            "description": current_description,
            "passed": eval_results["summary"]["passed"],
            "failed": eval_results["summary"]["failed"],
            "total": eval_results["summary"]["total"],
            "results": eval_results["results"],
        }],
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
