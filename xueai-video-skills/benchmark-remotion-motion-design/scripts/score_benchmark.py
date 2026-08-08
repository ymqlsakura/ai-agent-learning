from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


WEIGHTS = {
    "compositionHierarchy": 20,
    "motionIntent": 15,
    "processVisibility": 15,
    "narrationSync": 15,
    "brandConsistency": 10,
    "contentClarity": 10,
    "reuseSpeed": 10,
    "renderReliability": 5,
}

REQUIRED_GATES = (
    "buildPass",
    "deterministicRender",
    "audioPass",
    "accurateMaterials",
    "safeReadableText",
    "cueSyncPass",
    "processVisible",
)


def _validate_score(value: Any, name: str, variant_id: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{variant_id}: score {name} must be numeric")
    score = float(value)
    if score < 0 or score > 10:
        raise ValueError(f"{variant_id}: score {name} must be between 0 and 10")
    return score


def evaluate(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if sum(WEIGHTS.values()) != 100:
        raise RuntimeError("Benchmark weights must total 100")

    variants = payload.get("variants")
    if not isinstance(variants, list) or not variants:
        raise ValueError("scorecard must contain a non-empty variants array")

    seen_ids: set[str] = set()
    results: list[dict[str, Any]] = []
    for variant in variants:
        variant_id = variant.get("id")
        if not isinstance(variant_id, str) or not variant_id.strip():
            raise ValueError("every variant needs a non-empty id")
        if variant_id in seen_ids:
            raise ValueError(f"duplicate variant id: {variant_id}")
        seen_ids.add(variant_id)

        gates = variant.get("gates", {})
        missing_gates = [name for name in REQUIRED_GATES if name not in gates]
        if missing_gates:
            raise ValueError(f"{variant_id}: missing gates: {', '.join(missing_gates)}")
        failed_gates = [name for name in REQUIRED_GATES if gates.get(name) is not True]

        scores = variant.get("scores", {})
        missing_scores = [name for name in WEIGHTS if name not in scores]
        if missing_scores:
            raise ValueError(f"{variant_id}: missing scores: {', '.join(missing_scores)}")

        total = sum(
            _validate_score(scores[name], name, variant_id) * weight / 10
            for name, weight in WEIGHTS.items()
        )
        results.append(
            {
                "id": variant_id,
                "eligible": not failed_gates,
                "failedGates": failed_gates,
                "score": round(total, 2),
                "metrics": variant.get("metrics", {}),
            }
        )

    return sorted(results, key=lambda item: (item["eligible"], item["score"]), reverse=True)


def to_markdown(results: list[dict[str, Any]]) -> str:
    lines = [
        "# Remotion motion-design benchmark",
        "",
        "| Rank | Variant | Eligible | Score | Failed gates |",
        "|---:|---|---|---:|---|",
    ]
    for index, result in enumerate(results, start=1):
        failed = ", ".join(result["failedGates"]) or "None"
        eligible = "Yes" if result["eligible"] else "No"
        lines.append(
            f"| {index} | {result['id']} | {eligible} | {result['score']:.2f} | {failed} |"
        )
    lines.extend(
        [
            "",
            "Only eligible variants may be promoted. If two eligible variants are within three points, use the blind user preference as the tie-breaker.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Score Remotion motion-design variants")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    markdown = to_markdown(evaluate(payload))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(markdown, encoding="utf-8")
    else:
        print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

