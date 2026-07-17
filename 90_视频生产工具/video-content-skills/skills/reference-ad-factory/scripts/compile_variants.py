#!/usr/bin/env python3
"""Validate and compile controlled variant content into executable batch manifests."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise SystemExit(f"Required file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def text_blob(variant: dict[str, Any]) -> str:
    values = [variant.get("voiceover_text", "")]
    for scene in variant.get("scenes", []):
        values.extend([scene.get("title", ""), scene.get("caption", ""), scene.get("narration", "")])
    return "\n".join(str(value) for value in values).lower()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--content", type=Path)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    project = args.project.expanduser().resolve()
    plan_dir = project / "03_脚本与方案"
    content_path = (args.content or plan_dir / "phase2/variant-content.json").expanduser().resolve()
    intake = load(plan_dir / "intake.json")
    product = load(plan_dir / "product-brief.json")
    production = load(plan_dir / "production-plan.json")
    content = load(content_path)

    required_intake = ["ownership_authorized", "target_audience", "platform", "language", "aspect_ratio", "cost_authority"]
    missing_intake = [key for key in required_intake if not intake.get(key)]
    if missing_intake:
        raise SystemExit(f"Incomplete intake fields: {', '.join(missing_intake)}")
    if intake["ownership_authorized"] is not True:
        raise SystemExit("Reference ownership or processing authority is not confirmed")

    facts = {item["id"]: item["statement"] for item in product.get("verified_facts", [])}
    if not facts:
        raise SystemExit("product-brief.json requires verified_facts with stable IDs")
    expected = {item["variant_id"]: item for item in production["variants"]}
    supplied = {item["variant_id"]: item for item in content.get("variants", [])}
    if set(expected) != set(supplied):
        raise SystemExit(f"Variant IDs do not match production plan: expected {sorted(expected)}, got {sorted(supplied)}")

    prohibited = [value.lower() for value in product.get("prohibited_phrases", [])]
    assets = content.get("assets", {})
    voices = content.get("voices", {})
    compiled: list[dict[str, Any]] = []
    for variant_id in sorted(expected):
        source = supplied[variant_id]
        strategy = source.get("strategy")
        expected_strategy = expected[variant_id]["strategy"]["id"]
        if strategy != expected_strategy:
            raise SystemExit(f"{variant_id}: strategy must be {expected_strategy}, got {strategy}")
        scenes = source.get("scenes", [])
        if not scenes:
            raise SystemExit(f"{variant_id}: no scenes")
        duration = round(sum(float(scene["duration_seconds"]) for scene in scenes), 3)
        if duration < 20 or duration > 60:
            raise SystemExit(f"{variant_id}: final duration {duration}s is outside 20-60s")
        unknown_facts = sorted(set(source.get("claim_fact_ids", [])) - set(facts))
        if unknown_facts:
            raise SystemExit(f"{variant_id}: unknown fact IDs {unknown_facts}")
        used_assets = {scene["asset"] for scene in scenes}
        unknown_assets = sorted(used_assets - set(assets))
        if unknown_assets:
            raise SystemExit(f"{variant_id}: unknown asset IDs {unknown_assets}")
        blob = text_blob(source)
        hits = [phrase for phrase in prohibited if phrase and phrase in blob]
        if hits:
            raise SystemExit(f"{variant_id}: prohibited phrases found {hits}")
        compiled.append({
            **source,
            "duration_seconds": duration,
            "voiceover_path": voices.get(variant_id),
            "verified_claims": {fact_id: facts[fact_id] for fact_id in source.get("claim_fact_ids", [])},
            "output": f"06_成片/phase2/{variant_id}.mp4",
        })

    manifest = {
        "schema_version": 1,
        "project_root": ".",
        "video": {"width": 1080, "height": 1920, "fps": 24},
        "assets": assets,
        "variants": compiled,
        "quality": {"loudness_lufs": -16, "true_peak_dbfs": -1.5},
        "intake": str((plan_dir / "intake.json").relative_to(project)),
        "product_brief": str((plan_dir / "product-brief.json").relative_to(project)),
        "content_source": str(content_path.relative_to(project)),
    }
    summary = {
        "status": "valid",
        "variants": len(compiled),
        "durations": {item["variant_id"]: item["duration_seconds"] for item in compiled},
        "shared_asset_count": len(assets),
        "voice_assets_expected": sum(bool(item.get("voiceover_path")) for item in compiled),
    }
    if args.check_only:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return

    phase_dir = plan_dir / "phase2"
    output = phase_dir / "batch-manifest.json"
    if output.exists() and not args.force:
        raise SystemExit(f"Compiled manifest already exists: {output}; pass --force to replace it")
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    variants_dir = phase_dir / "variants"
    variants_dir.mkdir(parents=True, exist_ok=True)
    for item in compiled:
        target = variants_dir / item["variant_id"]
        target.mkdir(parents=True, exist_ok=True)
        (target / "shot-plan.json").write_text(json.dumps(item, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        lines = [f"# {item['variant_id']} - {item['strategy']}", "", "## Voiceover", "", item.get("voiceover_text", ""), "", "## Scenes", ""]
        for index, scene in enumerate(item["scenes"], start=1):
            lines.append(f"{index}. {scene['title']} | {scene['duration_seconds']}s | {scene['caption']}")
        (target / "script.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
