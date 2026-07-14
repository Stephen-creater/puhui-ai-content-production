#!/usr/bin/env python3
"""Assemble controlled variants from shared clips, voiceovers, and a compiled manifest."""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import time
from pathlib import Path
from typing import Any


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def probe_duration(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(result.stdout.strip())


def has_audio(path: Path) -> bool:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=index", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True,
    )
    return result.returncode == 0 and bool(result.stdout.strip())


def ass_text(value: str) -> str:
    return value.replace("\\", r"\\").replace("{", r"\{").replace("}", r"\}").replace("\n", r"\N")


def write_ass(path: Path, scenes: list[dict[str, Any]], width: int, height: int) -> None:
    lines = [
        "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {width}", f"PlayResY: {height}",
        "ScaledBorderAndShadow: yes", "WrapStyle: 2", "", "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        "Style: Title,Arial,70,&H0000D8FF,&H0000D8FF,&H00141414,&H88000000,-1,0,0,0,100,100,0,0,1,6,2,8,70,70,135,1",
        "Style: Caption,Arial,50,&H00FFFFFF,&H00FFFFFF,&H00141414,&H88000000,-1,0,0,0,100,100,0,0,1,5,2,2,72,72,145,1",
        "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    cursor = 0.0
    for scene in scenes:
        end = cursor + float(scene["duration_seconds"])
        def stamp(seconds: float) -> str:
            centiseconds = int(round(seconds * 100))
            return f"{centiseconds // 360000}:{(centiseconds // 6000) % 60:02d}:{(centiseconds // 100) % 60:02d}.{centiseconds % 100:02d}"
        lines.append(f"Dialogue: 0,{stamp(cursor)},{stamp(end)},Title,,0,0,0,,{ass_text(scene['title'])}")
        lines.append(f"Dialogue: 0,{stamp(cursor)},{stamp(end)},Caption,,0,0,0,,{ass_text(scene['caption'])}")
        cursor = end
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def atempo_chain(factor: float) -> str:
    factors: list[float] = []
    while factor > 2.0:
        factors.append(2.0)
        factor /= 2.0
    while factor < 0.5:
        factors.append(0.5)
        factor /= 0.5
    factors.append(factor)
    return ",".join(f"atempo={value:.6f}" for value in factors)


def resolve(project: Path, value: str) -> Path:
    path = Path(value).expanduser()
    return path.resolve() if path.is_absolute() else (project / path).resolve()


def validate(
    manifest: dict[str, Any], project: Path, allow_missing_voice: bool, allow_missing_visuals: bool
) -> dict[str, Any]:
    missing_visuals: list[str] = []
    missing_voices: list[str] = []
    assets = manifest["assets"]
    for value in assets.values():
        if not resolve(project, value).is_file():
            missing_visuals.append(value)
    for variant in manifest["variants"]:
        voice = variant.get("voiceover_path")
        if voice and not resolve(project, voice).is_file():
            missing_voices.append(voice)
    if missing_visuals and not allow_missing_visuals:
        raise SystemExit(f"Missing visual assets: {missing_visuals}")
    if missing_voices and not allow_missing_voice:
        raise SystemExit(f"Missing voice assets: {missing_voices}")
    return {
        "variants": len(manifest["variants"]),
        "shared_assets": len(assets),
        "missing_voice_assets": missing_voices,
        "missing_visual_assets": missing_visuals,
        "durations": {item["variant_id"]: item["duration_seconds"] for item in manifest["variants"]},
    }


def assemble_variant(manifest: dict[str, Any], project: Path, variant: dict[str, Any], force: bool) -> dict[str, Any]:
    started = time.perf_counter()
    video = manifest["video"]
    width, height, fps = int(video["width"]), int(video["height"]), int(video["fps"])
    output = resolve(project, variant["output"])
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists() and not force:
        return {"variant_id": variant["variant_id"], "output": str(output), "status": "reused", "seconds": 0}
    work = project / "04_postproduction/phase2/work"
    work.mkdir(parents=True, exist_ok=True)
    ass_path = work / f"{variant['variant_id']}.ass"
    write_ass(ass_path, variant["scenes"], width, height)

    inputs: list[str] = []
    filters: list[str] = []
    assets = manifest["assets"]
    for index, scene in enumerate(variant["scenes"]):
        clip = resolve(project, assets[scene["asset"]])
        inputs.extend(["-i", str(clip)])
        start = float(scene.get("source_start_seconds", 0))
        duration = float(scene["duration_seconds"])
        filters.append(
            f"[{index}:v]trim=start={start}:duration={duration},setpts=PTS-STARTPTS,"
            f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={fps},format=yuv420p[v{index}]"
        )
        if scene.get("use_source_audio") and has_audio(clip):
            filters.append(
                f"[{index}:a]atrim=start={start}:duration={duration},asetpts=PTS-STARTPTS,"
                f"aresample=48000,aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,"
                f"apad=whole_dur={duration}[a{index}]"
            )
        else:
            filters.append(f"anullsrc=r=48000:cl=stereo,atrim=duration={duration},asetpts=PTS-STARTPTS[a{index}]")
    labels = "".join(f"[v{index}][a{index}]" for index in range(len(variant["scenes"])))
    filters.append(f"{labels}concat=n={len(variant['scenes'])}:v=1:a=1[basev][basea]")
    escaped_ass = str(ass_path).replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
    filters.append(f"[basev]ass=filename='{escaped_ass}'[outv]")

    total_duration = float(variant["duration_seconds"])
    voice = variant.get("voiceover_path")
    if voice:
        voice_path = resolve(project, voice)
        voice_index = len(variant["scenes"])
        inputs.extend(["-i", str(voice_path)])
        target = float(variant["voiceover_target_seconds"])
        factor = probe_duration(voice_path) / target
        delay = int(round(float(variant.get("voiceover_start_seconds", 0)) * 1000))
        filters.append(
            f"[{voice_index}:a]{atempo_chain(factor)},loudnorm=I=-16:TP=-1.5:LRA=11,"
            f"aresample=48000,aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,"
            f"adelay={delay}|{delay},apad,atrim=duration={total_duration}[voice]"
        )
        filters.append("[basea][voice]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=11[outa]")
    else:
        filters.append("[basea]loudnorm=I=-16:TP=-1.5:LRA=11[outa]")

    command = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *inputs,
        "-filter_complex", ";".join(filters), "-map", "[outv]", "-map", "[outa]",
        "-t", str(total_duration), "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(output),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr[-2000:])
    return {
        "variant_id": variant["variant_id"],
        "output": str(output),
        "status": "assembled",
        "duration_seconds": round(probe_duration(output), 3),
        "wall_seconds": round(time.perf_counter() - started, 3),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--allow-missing-voice", action="store_true")
    parser.add_argument("--allow-missing-visuals", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    manifest_path = args.manifest.expanduser().resolve()
    manifest = load(manifest_path)
    project = manifest_path.parents[2]
    summary = validate(manifest, project, args.allow_missing_voice, args.allow_missing_visuals)
    if args.dry_run:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return
    if summary["missing_voice_assets"]:
        raise SystemExit("Cannot assemble while voice assets are missing")
    if summary["missing_visual_assets"]:
        raise SystemExit("Cannot assemble while visual assets are missing")
    results = [assemble_variant(manifest, project, item, args.force) for item in manifest["variants"]]
    report = {"ok": True, "results": results, "total_wall_seconds": round(sum(item.get("wall_seconds", 0) for item in results), 3)}
    report_path = project / "06_reports/phase2-assembly-report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
