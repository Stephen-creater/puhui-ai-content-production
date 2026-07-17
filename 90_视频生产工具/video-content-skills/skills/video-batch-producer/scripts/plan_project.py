#!/usr/bin/env python3
"""Create a resumable script-to-video project manifest."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path


ASPECTS = {
    "9:16": {"image_width": 1440, "image_height": 2560, "video_width": 720, "video_height": 1280},
    "16:9": {"image_width": 2560, "image_height": 1440, "video_width": 1280, "video_height": 720},
    "1:1": {"image_width": 2048, "image_height": 2048, "video_width": 720, "video_height": 720},
}

VIDEO_DIMS = {
    "480p": {"9:16": (480, 854), "16:9": (854, 480), "1:1": (480, 480)},
    "720p": {"9:16": (720, 1280), "16:9": (1280, 720), "1:1": (720, 720)},
    "1080p": {"9:16": (1080, 1920), "16:9": (1920, 1080), "1:1": (1080, 1080)},
}

MIN_FINAL_DURATION = 20
MAX_RECOMMENDED_DURATION = 60


def read_script(value: str) -> tuple[str, str]:
    path = Path(value).expanduser()
    if path.is_file():
        return path.read_text(encoding="utf-8").strip(), str(path.resolve())
    return value.strip(), "inline"


def split_units(script: str) -> list[str]:
    units = [part.strip() for part in re.split(r"(?<=[。！？!?；;])|\n+", script) if part.strip()]
    return units or [script.strip()]


def group_units(units: list[str], target: int) -> list[str]:
    target = max(1, min(target, len(units)))
    groups: list[list[str]] = [[] for _ in range(target)]
    for index, unit in enumerate(units):
        bucket = min(target - 1, index * target // len(units))
        groups[bucket].append(unit)
    return ["".join(group).strip() for group in groups if group]


def build_scene(index: int, text: str, duration: int, generation_duration: int = 10) -> dict:
    clean = re.sub(r"\s+", " ", text).strip()
    return {
        "id": index,
        "narration": clean,
        "duration_seconds": duration,
        "generation_duration_seconds": generation_duration,
        "keyframe_prompt": (
            "Vertical cinematic advertising keyframe, one coherent scene, realistic lighting, "
            f"clear subject, no embedded text, no watermark. Story beat: {clean}"
        ),
        "video_prompt": (
            "Animate this keyframe into a polished short advertising shot. Preserve subject identity, "
            "product geometry, colors, and background continuity. Use one restrained camera movement "
            f"and natural motion. Story beat: {clean}"
        ),
        "negative_prompt": "distorted product, extra limbs, warped hands, unreadable text, watermark, flicker, jump cut",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--script", required=True, help="UTF-8 script file or inline script text")
    parser.add_argument("--output", required=True, help="Project directory")
    parser.add_argument("--variants", type=int, default=2)
    parser.add_argument("--scenes", type=int, default=4)
    parser.add_argument("--scene-duration", type=int, default=5)
    parser.add_argument("--aspect-ratio", choices=ASPECTS, default="9:16")
    parser.add_argument("--image-model", default="seedream-5.0-lite")
    parser.add_argument(
        "--video-model",
        choices=("grok-imagine-video-1.5-fast", "grok-imagine-video-1.5-preview"),
        default="grok-imagine-video-1.5-fast",
    )
    parser.add_argument("--generation-duration", type=int)
    parser.add_argument("--video-resolution", choices=VIDEO_DIMS, default="720p")
    args = parser.parse_args()

    if args.variants < 1 or args.scenes < 1 or args.scene_duration < 1:
        parser.error("variants, scenes, and scene-duration must be positive")
    generation_duration = args.generation_duration
    if generation_duration is None:
        generation_duration = 15 if args.video_model.endswith("-preview") else 10
    if args.video_model.endswith("-fast") and generation_duration not in (6, 10):
        parser.error("Fast generation-duration must be 6 or 10")
    if args.video_model.endswith("-preview") and not 1 <= generation_duration <= 15:
        parser.error("Preview generation-duration must be between 1 and 15")

    script, source = read_script(args.script)
    if not script:
        parser.error("script is empty")

    output = Path(args.output).expanduser().resolve()
    manifest_path = output / "project.json"
    if manifest_path.exists():
        parser.error(f"project already exists: {manifest_path}")

    units = group_units(split_units(script), args.scenes)
    dims = dict(ASPECTS[args.aspect_ratio])
    dims["video_width"], dims["video_height"] = VIDEO_DIMS[args.video_resolution][args.aspect_ratio]
    project = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "script_source": source,
        "script": script,
        "variants": args.variants,
        "aspect_ratio": args.aspect_ratio,
        "provider": "mixed",
        "image_provider": "tokendance",
        "video_provider": "nanyao",
        "image_model": args.image_model,
        "video_model": args.video_model,
        "video_protocol": "nanyao:videos",
        "video_generation_duration_seconds": generation_duration,
        "video_resolution": args.video_resolution,
        **dims,
        "fps": 24,
        "scenes": [
            build_scene(index + 1, text, args.scene_duration, generation_duration)
            for index, text in enumerate(units)
        ],
    }
    total_jobs = args.variants * len(project["scenes"])
    expected_duration = sum(scene["duration_seconds"] for scene in project["scenes"])
    if expected_duration < MIN_FINAL_DURATION:
        parser.error(
            f"planned final duration is {expected_duration}s; minimum is {MIN_FINAL_DURATION}s. "
            "Increase scenes or scene-duration."
        )
    output.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(project, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for folder in ("keyframes", "clips", "output"):
        (output / folder).mkdir(exist_ok=True)
    summary = {
        "project": str(output),
        "scenes": len(project["scenes"]),
        "variants": args.variants,
        "keyframe_jobs": total_jobs,
        "video_jobs": total_jobs,
        "final_videos": args.variants,
        "expected_duration_seconds": expected_duration,
        "duration_policy": {
            "minimum_seconds": MIN_FINAL_DURATION,
            "recommended_maximum_seconds": MAX_RECOMMENDED_DURATION,
            "status": "within_recommended_range" if expected_duration <= MAX_RECOMMENDED_DURATION else "over_recommended_maximum",
        },
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
