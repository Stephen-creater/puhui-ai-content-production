#!/usr/bin/env python3
"""Create controlled, machine-readable variant plans for a reference ad project."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


STRATEGIES = [
    {
        "id": "pain-result",
        "hook": "Show the problem and protected result immediately",
        "controlled_changes": ["hook wording", "opening visual", "proof emphasis"],
    },
    {
        "id": "efficiency",
        "hook": "Lead with time saved or fewer cleanup steps",
        "controlled_changes": ["benefit order", "narration", "CTA"],
    },
    {
        "id": "product-structure",
        "hook": "Lead with the product feature that enables the result",
        "controlled_changes": ["macro product shot", "feature explanation", "proof order"],
    },
    {
        "id": "professional-recommendation",
        "hook": "Open with a credible professional recommendation",
        "controlled_changes": ["presenter opening", "authority cue", "CTA"],
    },
    {
        "id": "before-after",
        "hook": "Open with a clear before and after comparison",
        "controlled_changes": ["result framing", "edit order", "caption language"],
    },
]


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise SystemExit(f"Required JSON not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--variants", type=int)
    parser.add_argument("--template-dna", type=Path)
    parser.add_argument("--duration-target", type=float)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="Print the plan without writing production-plan.json")
    args = parser.parse_args()

    project = args.project.expanduser().resolve()
    config = read_json(project / "project-config.json")
    template_path = (args.template_dna or project / "02_plan/template-dna.json").expanduser().resolve()
    template = read_json(template_path)
    count = args.variants or int(config.get("variant_count", 3))
    if count < 1:
        raise SystemExit("Variant count must be at least 1")

    duration_range = template.get("duration_range_seconds", [20, 60])
    duration_target = args.duration_target or template.get("duration_target_seconds") or 36
    if duration_target < 20:
        raise SystemExit("Target duration must be at least 20 seconds")
    if duration_target > 60:
        print("Warning: target duration exceeds the recommended 60-second maximum")

    output = project / "02_plan/production-plan.json"
    if output.exists() and not args.force and not args.dry_run:
        raise SystemExit(f"Production plan already exists: {output}; pass --force to replace it")

    variants = []
    for index in range(count):
        strategy = STRATEGIES[index % len(STRATEGIES)]
        variants.append({
            "variant_id": f"variant-{index + 1:02d}",
            "status": "script_required",
            "strategy": strategy,
            "duration_target_seconds": duration_target,
            "language": config.get("language", "en"),
            "aspect_ratio": config.get("aspect_ratio", "9:16"),
            "must_preserve": [
                "product facts",
                "product geometry",
                "operation order",
                "prohibited claims",
                "delivery specification",
            ],
            "required_assets": [
                "finished script",
                "scene plan",
                "keyframes",
                "generated clips",
                "voice and dialogue",
                "captions and claims",
                "final video",
                "verify report",
            ],
        })

    plan = {
        "schema_version": 1,
        "project": str(project),
        "template_dna": str(template_path),
        "duration_range_seconds": duration_range,
        "variant_count": count,
        "variants": variants,
        "generation_order": [
            "scripts",
            "keyframes",
            "keyframe_review",
            "video",
            "voice_and_native_dialogue",
            "postproduction",
            "verification",
        ],
        "batch_quality_gate": "Every variant must have a declared editorial difference and pass the same product truth checks",
    }
    if args.dry_run:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
    else:
        output.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(output)


if __name__ == "__main__":
    main()
