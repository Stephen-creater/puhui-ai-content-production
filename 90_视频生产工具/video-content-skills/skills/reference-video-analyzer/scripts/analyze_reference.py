#!/usr/bin/env python3
"""Extract deterministic evidence from a short reference video."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, capture_output=True, check=True)


def require_binary(name: str) -> None:
    if shutil.which(name) is None:
        raise SystemExit(f"Required binary not found: {name}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ratio(value: str | None) -> float | None:
    if not value or value in {"0/0", "N/A"}:
        return None
    if "/" in value:
        numerator, denominator = value.split("/", 1)
        return float(numerator) / float(denominator) if float(denominator) else None
    return float(value)


def probe(path: Path) -> dict[str, Any]:
    result = run([
        "ffprobe", "-v", "error", "-show_streams", "-show_format",
        "-of", "json", str(path),
    ])
    return json.loads(result.stdout)


def detect_cuts(path: Path, threshold: float, duration: float) -> list[float]:
    command = [
        "ffmpeg", "-hide_banner", "-i", str(path),
        "-vf", f"select='gt(scene,{threshold})',showinfo",
        "-an", "-f", "null", "-",
    ]
    result = subprocess.run(command, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(result.stderr[-2000:])
    cuts = [float(value) for value in re.findall(r"pts_time:([0-9.]+)", result.stderr)]
    return sorted({round(value, 3) for value in cuts if 0.05 < value < duration - 0.05})


def segments(cuts: list[float], duration: float) -> list[dict[str, float | int]]:
    boundaries = [0.0, *cuts, round(duration, 3)]
    output: list[dict[str, float | int]] = []
    for index, (start, end) in enumerate(zip(boundaries, boundaries[1:]), start=1):
        output.append({
            "id": index,
            "start_seconds": round(start, 3),
            "end_seconds": round(end, 3),
            "duration_seconds": round(end - start, 3),
        })
    return output


def make_contact_sheet(path: Path, output: Path, duration: float, requested_interval: float) -> dict[str, Any]:
    interval = max(0.25, requested_interval)
    samples = max(1, math.ceil(duration / interval))
    if samples > 60:
        interval = duration / 60
        samples = 60
    columns = 4
    rows = math.ceil(samples / columns)
    filter_graph = (
        f"fps=1/{interval:.6f},scale=320:-2,"
        f"tile={columns}x{rows}:padding=8:margin=8:color=white"
    )
    result = subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(path), "-vf", filter_graph, "-frames:v", "1", str(output),
    ], text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(result.stderr[-2000:])
    return {
        "path": str(output),
        "interval_seconds": round(interval, 3),
        "sample_count": samples,
        "columns": columns,
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--scene-threshold", type=float, default=0.30)
    parser.add_argument("--contact-interval", type=float, default=1.0)
    parser.add_argument("--transcript-file", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    require_binary("ffmpeg")
    require_binary("ffprobe")
    source = args.input.expanduser().resolve()
    if not source.is_file():
        raise SystemExit(f"Input video not found: {source}")
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "reference-analysis.json"
    contact_path = output_dir / "contact-sheet-auto.jpg"
    if not args.overwrite and (report_path.exists() or contact_path.exists()):
        if report_path.is_file() and contact_path.is_file():
            existing = json.loads(report_path.read_text(encoding="utf-8"))
            if existing.get("source", {}).get("sha256") == sha256(source):
                print(json.dumps({"status": "reused", "report": str(report_path)}, ensure_ascii=False))
                return
        raise SystemExit("Analysis output exists for different or incomplete input; pass --overwrite to replace it")

    raw_probe = probe(source)
    video = next((item for item in raw_probe.get("streams", []) if item.get("codec_type") == "video"), {})
    audio = next((item for item in raw_probe.get("streams", []) if item.get("codec_type") == "audio"), None)
    duration = float(raw_probe.get("format", {}).get("duration") or video.get("duration") or 0)
    if duration <= 0:
        raise SystemExit("Could not determine a positive video duration")

    cuts = detect_cuts(source, args.scene_threshold, duration)
    editorial_segments = segments(cuts, duration)
    transcript: dict[str, Any] = {"status": "not_provided"}
    if args.transcript_file:
        transcript_source = args.transcript_file.expanduser().resolve()
        if not transcript_source.is_file():
            raise SystemExit(f"Transcript not found: {transcript_source}")
        transcript_path = output_dir / "transcript.txt"
        transcript_path.write_text(transcript_source.read_text(encoding="utf-8"), encoding="utf-8")
        transcript = {"status": "provided", "path": str(transcript_path)}

    report = {
        "schema_version": 1,
        "source": {
            "path": str(source),
            "filename": source.name,
            "size_bytes": source.stat().st_size,
            "sha256": sha256(source),
        },
        "technical": {
            "duration_seconds": round(duration, 3),
            "video": {
                "codec": video.get("codec_name"),
                "width": video.get("width"),
                "height": video.get("height"),
                "fps": ratio(video.get("avg_frame_rate")),
                "pixel_format": video.get("pix_fmt"),
            },
            "audio": None if audio is None else {
                "codec": audio.get("codec_name"),
                "sample_rate": int(audio["sample_rate"]) if audio.get("sample_rate") else None,
                "channels": audio.get("channels"),
            },
        },
        "scene_detection": {
            "threshold": args.scene_threshold,
            "cut_times_seconds": cuts,
            "segments": editorial_segments,
            "segment_count": len(editorial_segments),
            "average_segment_seconds": round(duration / len(editorial_segments), 3),
            "requires_editorial_review": True,
        },
        "contact_sheet": make_contact_sheet(source, contact_path, duration, args.contact_interval),
        "transcript": transcript,
        "enrichment_required": [
            "transcript_and_speaker_roles",
            "on_screen_text",
            "shot_function",
            "action_progression",
            "information_layers",
            "audio_structure",
            "template_dna",
        ],
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(report_path)


if __name__ == "__main__":
    main()
