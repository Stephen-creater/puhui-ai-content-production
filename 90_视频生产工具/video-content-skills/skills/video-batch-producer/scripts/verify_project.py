#!/usr/bin/env python3
"""Verify expected video project artifacts with ffprobe."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


def enabled(value: Any) -> bool:
    return value is True or str(value).lower() in {"1", "true", "on", "yes"}


def scenes_for_variant(project: dict[str, Any], variant: int) -> list[dict[str, Any]]:
    if "variant_scenes" not in project:
        return project["scenes"]
    for item in project["variant_scenes"]:
        if int(item["variant"]) == int(variant):
            return item["scenes"]
    raise ValueError(f"missing scene plan for variant {variant}")


def expected_duration(project: dict[str, Any], variant: int) -> float:
    return sum(float(scene["duration_seconds"]) for scene in scenes_for_variant(project, variant))


def probe(path: Path) -> dict[str, Any]:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries",
            "format=duration,size:stream=index,codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels",
            "-of", "json", str(path),
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        return {"ok": False, "error": result.stderr.strip()}
    data = json.loads(result.stdout)
    video = next((stream for stream in data.get("streams", []) if stream.get("codec_type") == "video"), None)
    audio = next((stream for stream in data.get("streams", []) if stream.get("codec_type") == "audio"), None)
    return {
        "ok": video is not None and float(data.get("format", {}).get("duration", 0)) > 0,
        "duration": float(data.get("format", {}).get("duration", 0)),
        "size_bytes": int(data.get("format", {}).get("size", 0)),
        "video": video,
        "audio": audio,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--check-only", action="store_true", help="Print verification without writing verify-report.json")
    args = parser.parse_args()
    root = Path(args.project).expanduser().resolve()
    project_path = root / "project.json"
    if not project_path.is_file():
        parser.error(f"missing {project_path}")
    project = json.loads(project_path.read_text(encoding="utf-8"))

    if project.get("asset_bank"):
        clips: list[dict[str, Any]] = []
        for variant in range(1, int(project["variants"]) + 1):
            for scene in scenes_for_variant(project, variant):
                path = root / "clips" / f"variant-{variant:02d}" / f"scene-{int(scene['id']):02d}.mp4"
                item: dict[str, Any] = {
                    "variant": variant,
                    "scene": int(scene["id"]),
                    "path": str(path),
                    "exists": path.is_file(),
                }
                if path.is_file():
                    item.update(probe(path))
                    video = item.get("video") or {}
                    item["dimensions_match"] = (
                        video.get("width") == project["video_width"]
                        and video.get("height") == project["video_height"]
                    )
                    item["duration_plausible"] = item.get("duration", 0) >= float(scene["duration_seconds"])
                    item["audio_expected"] = enabled(scene.get("generate_audio", project.get("generate_audio")))
                    item["audio_present"] = item.get("audio") is not None
                    item["ok"] = bool(
                        item.get("ok")
                        and item["dimensions_match"]
                        and item["duration_plausible"]
                        and (not item["audio_expected"] or item["audio_present"])
                    )
                else:
                    item["ok"] = False
                clips.append(item)
        report = {"project": str(root), "asset_bank": True, "ok": all(item["ok"] for item in clips), "clips": clips}
        if not args.check_only:
            (root / "verify-report.json").write_text(
                json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["ok"] else 2

    checks: list[dict[str, Any]] = []
    for variant in range(1, int(project["variants"]) + 1):
        output = root / "output" / f"variant-{variant:02d}.mp4"
        item: dict[str, Any] = {"variant": variant, "path": str(output), "exists": output.is_file()}
        if output.is_file():
            item.update(probe(output))
            video = item.get("video") or {}
            item["dimensions_match"] = (
                video.get("width") == project["video_width"] and video.get("height") == project["video_height"]
            )
            expected = expected_duration(project, variant)
            item["duration_plausible"] = expected * 0.8 <= item.get("duration", 0) <= expected * 1.2
            item["audio_expected"] = bool(
                enabled(project.get("generate_audio"))
                or any(enabled(scene.get("generate_audio")) for scene in scenes_for_variant(project, variant))
            )
            item["audio_present"] = item.get("audio") is not None
            item["ok"] = bool(
                item.get("ok")
                and item["dimensions_match"]
                and item["duration_plausible"]
                and (not item["audio_expected"] or item["audio_present"])
            )
        else:
            item["ok"] = False
        checks.append(item)

    report = {"project": str(root), "ok": all(item["ok"] for item in checks), "outputs": checks}
    if not args.check_only:
        (root / "verify-report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
