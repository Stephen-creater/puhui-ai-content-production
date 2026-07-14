#!/usr/bin/env python3
"""Verify expected video project artifacts with ffprobe."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


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
    args = parser.parse_args()
    root = Path(args.project).expanduser().resolve()
    project_path = root / "project.json"
    if not project_path.is_file():
        parser.error(f"missing {project_path}")
    project = json.loads(project_path.read_text(encoding="utf-8"))

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
            expected = sum(scene["duration_seconds"] for scene in project["scenes"])
            item["duration_plausible"] = expected * 0.8 <= item.get("duration", 0) <= expected * 1.2
            item["audio_expected"] = bool(
                project.get("generate_audio")
                or any(scene.get("generate_audio") for scene in project["scenes"])
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
    (root / "verify-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
