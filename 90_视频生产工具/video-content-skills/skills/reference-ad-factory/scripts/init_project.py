#!/usr/bin/env python3
"""Initialize a durable local project for a reference-driven ad campaign."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path


DIRECTORIES = [
    "01_原始资料/reference_videos",
    "01_原始资料/product_images",
    "02_参考片拆解",
    "03_脚本与方案/variants",
    "04_AI生成工程",
    "05_后期制作",
    "06_成片",
    "07_验收报告",
    "08_场景单元",
]


def safe_name(value: str) -> str:
    cleaned = re.sub(r"[^\w.-]+", "-", value.strip(), flags=re.UNICODE).strip("-.")
    if not cleaned:
        raise SystemExit("Project name must contain a letter or number")
    return cleaned.lower()


def copy_inputs(sources: list[Path], destination: Path, prefix: str) -> list[str]:
    copied: list[str] = []
    for index, source_value in enumerate(sources, start=1):
        source = source_value.expanduser().resolve()
        if not source.is_file():
            raise SystemExit(f"Input not found: {source}")
        target = destination / f"{prefix}-{index:02d}{source.suffix.lower()}"
        if source != target.resolve():
            shutil.copy2(source, target)
        copied.append(str(target.resolve()))
    return copied


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--project-name", required=True)
    parser.add_argument("--reference-video", action="append", type=Path, default=[])
    parser.add_argument("--product-image", action="append", type=Path, default=[])
    parser.add_argument("--variants", type=int, default=3)
    parser.add_argument("--language", default="en")
    parser.add_argument("--aspect-ratio", default="9:16")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if not args.reference_video:
        raise SystemExit("Provide at least one --reference-video")
    if args.variants < 1:
        raise SystemExit("--variants must be at least 1")

    project = args.output_root.expanduser().resolve() / safe_name(args.project_name)
    config_path = project / "project-config.json"
    if config_path.exists() and not args.force:
        raise SystemExit(f"Project already initialized: {project}; pass --force to refresh configuration")
    for relative in DIRECTORIES:
        (project / relative).mkdir(parents=True, exist_ok=True)

    references = copy_inputs(args.reference_video, project / "01_原始资料/reference_videos", "reference")
    images = copy_inputs(args.product_image, project / "01_原始资料/product_images", "product")
    config = {
        "schema_version": 1,
        "project_name": safe_name(args.project_name),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "reference_videos": references,
        "product_images": images,
        "variant_count": args.variants,
        "language": args.language,
        "aspect_ratio": args.aspect_ratio,
        "duration_policy": {"minimum_seconds": 20, "recommended_maximum_seconds": 60},
        "git_policy": {
            "track": ["plans", "scripts", "keyframes", "reports", "skills"],
            "local_only": ["videos", "audio", "presentations", "provider_metadata", "credentials"],
        },
        "status": "intake_complete",
    }
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    brief_path = project / "03_脚本与方案/product-brief.template.json"
    if args.force or not brief_path.exists():
        brief = {
            "product_name": "",
            "verified_facts": [],
            "correct_operation_order": [],
            "required_claims": [],
            "prohibited_claims": [],
            "visual_invariants": [],
            "target_audience": "",
            "call_to_action": "",
        }
        brief_path.write_text(json.dumps(brief, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(project)


if __name__ == "__main__":
    main()
