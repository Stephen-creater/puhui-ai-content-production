#!/usr/bin/env python3
"""Record a human visual decision for one generated keyframe."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


CRITERIA = (
    "continuous_film_no_holes",
    "full_object_coverage",
    "tape_film_continuity",
    "tape_on_valid_surface",
    "single_integrated_product",
    "no_visual_artifacts",
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, value: dict) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def image_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--task", required=True, help="Task key such as v01-s01")
    decision = parser.add_mutually_exclusive_group(required=True)
    decision.add_argument("--approve", action="store_true")
    decision.add_argument("--reject", action="store_true")
    parser.add_argument("--notes", required=True, help="Concrete visual evidence for the decision")
    parser.add_argument("--reviewer", default="human-visual-review")
    args = parser.parse_args()

    root = Path(args.project).expanduser().resolve()
    try:
        variant_text, scene_text = args.task.split("-", 1)
        variant = int(variant_text.removeprefix("v"))
        scene = int(scene_text.removeprefix("s"))
    except ValueError as exc:
        parser.error(f"invalid --task {args.task!r}; expected vNN-sNN")
        raise AssertionError from exc
    keyframe = root / "keyframes" / f"variant-{variant:02d}" / f"scene-{scene:02d}.png"
    if not keyframe.is_file():
        parser.error(f"missing keyframe: {keyframe}")

    review_path = root / "keyframe-review.json"
    document = load_json(review_path) if review_path.exists() else {
        "schema_version": 1,
        "criteria_version": "product-keyframe-v1",
        "reviews": {},
    }
    approved = bool(args.approve)
    document["reviews"][args.task] = {
        "approved": approved,
        "image_sha256": image_hash(keyframe),
        "checks": {name: approved for name in CRITERIA},
        "notes": args.notes,
        "reviewer": args.reviewer,
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
    }
    document["updated_at"] = datetime.now(timezone.utc).isoformat()
    save_json(review_path, document)
    print(json.dumps({"task": args.task, "approved": approved, "review_file": str(review_path)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
