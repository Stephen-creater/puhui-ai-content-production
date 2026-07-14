#!/usr/bin/env python3
"""Run or inspect a resumable batch keyframe-to-video pipeline."""

from __future__ import annotations

import argparse
import base64
import concurrent.futures
import getpass
import json
import mimetypes
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, value: dict[str, Any]) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


GATEWAY = "https://tokendance.space/gateway"


def require_api_key() -> str:
    if key := os.environ.get("TOKENDANCE_API_KEY"):
        return key
    result = subprocess.run(
        ["security", "find-generic-password", "-a", getpass.getuser(),
         "-s", "video-content-skills/tokendance", "-w"],
        capture_output=True, text=True,
    )
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    raise RuntimeError(
        "TOKENDANCE_API_KEY is not set and no macOS Keychain item exists for "
        "service video-content-skills/tokendance"
    )


def api_json(path: str, key: str, payload: dict[str, Any] | None = None, timeout: int = 300) -> dict[str, Any]:
    request = urllib.request.Request(
        f"{GATEWAY}{path}",
        data=json.dumps(payload).encode("utf-8") if payload is not None else None,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST" if payload is not None else "GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")[:2000]
        raise RuntimeError(f"TokenDance HTTP {exc.code} for {path}: {body}") from exc


def dimensions(project: dict[str, Any]) -> tuple[int, int, int, int]:
    return (
        int(project["image_width"]),
        int(project["image_height"]),
        int(project["video_width"]),
        int(project["video_height"]),
    )


def task_paths(root: Path, variant: int, scene: int, create: bool = False) -> tuple[Path, Path]:
    variant_name = f"variant-{variant:02d}"
    keyframe = root / "keyframes" / variant_name / f"scene-{scene:02d}.png"
    clip = root / "clips" / variant_name / f"scene-{scene:02d}.mp4"
    if create:
        keyframe.parent.mkdir(parents=True, exist_ok=True)
        clip.parent.mkdir(parents=True, exist_ok=True)
    return keyframe, clip


def reference_image_value(value: str) -> str:
    if value.startswith(("http://", "https://", "data:")):
        return value
    path = Path(value).expanduser().resolve()
    if not path.is_file():
        raise RuntimeError(f"reference image does not exist: {path}")
    raw = path.read_bytes()
    if raw.startswith(b"\xff\xd8\xff"):
        mime = "image/jpeg"
    elif raw.startswith(b"\x89PNG\r\n\x1a\n"):
        mime = "image/png"
    else:
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    encoded = base64.b64encode(raw).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def generate_keyframe(
    project: dict[str, Any], scene: dict[str, Any], variant: int, output: Path, key: str
) -> str:
    width, height, _, _ = dimensions(project)
    prompt = f"{scene['keyframe_prompt']} Visual variation {variant}; preserve the same factual story beat."
    payload: dict[str, Any] = {
        "model": project["image_model"],
        "prompt": prompt,
        "n": 1,
        "size": f"{width}x{height}",
        "response_format": "url",
        "watermark": False,
    }
    if scene.get("reference_images"):
        payload["image"] = [reference_image_value(value) for value in scene["reference_images"]]
    response = api_json("/v1/images/generations", key, payload)
    item = response["data"][0]
    source_url = item.get("url")
    if not source_url:
        raise RuntimeError("TokenDance image response did not include data[0].url")
    with urllib.request.urlopen(source_url, timeout=180) as download:
        output.write_bytes(download.read())
    source_path = output.with_suffix(output.suffix + ".source.json")
    save_json(source_path, {"url": source_url, "model": response.get("model", project["image_model"]), "created_at": utc_now()})
    return source_url


def poll_video(key: str, job_id: str, timeout: int, interval: int = 10) -> tuple[str, dict[str, Any]]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        status = api_json(f"/ark/v3/generations/tasks/{job_id}", key)
        state = str(status.get("status", "")).lower()
        if state in {"succeeded", "completed", "success", "done"}:
            video_url = (status.get("content") or {}).get("video_url")
            if not video_url:
                raise RuntimeError(f"video job {job_id} completed without content.video_url")
            return video_url, status
        if state in {"failed", "cancelled", "canceled", "error"}:
            raise RuntimeError(f"video job {job_id} {state}: {status.get('error')}")
        time.sleep(interval)
    raise TimeoutError(f"video job {job_id} did not finish within {timeout}s")


def poll_kling_video(key: str, job_id: str, timeout: int, interval: int = 10) -> tuple[str, dict[str, Any]]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        status = api_json(f"/kling/v1/image2video/{job_id}", key)
        data = status.get("data") or {}
        state = str(data.get("task_status", "")).lower()
        if state in {"succeed", "succeeded", "completed", "success"}:
            videos = (data.get("task_result") or {}).get("videos") or []
            if not videos or not videos[0].get("url"):
                raise RuntimeError(f"Kling video job {job_id} completed without data.task_result.videos[0].url")
            return videos[0]["url"], status
        if state in {"failed", "cancelled", "canceled", "error"}:
            raise RuntimeError(f"Kling video job {job_id} {state}: {data.get('task_status_msg')}")
        time.sleep(interval)
    raise TimeoutError(f"Kling video job {job_id} did not finish within {timeout}s")


def generate_clip(
    project: dict[str, Any], scene: dict[str, Any], keyframe: Path, output: Path,
    timeout: int, key: str, source_url: str | None = None,
) -> dict[str, Any]:
    source_path = keyframe.with_suffix(keyframe.suffix + ".source.json")
    if not source_url and source_path.exists():
        source_url = load_json(source_path).get("url")
    if not source_url:
        raise RuntimeError(f"missing source URL metadata for {keyframe}; regenerate its keyframe")
    resolution = str(project.get("video_resolution", "720p"))
    generation_duration = int(scene.get("generation_duration_seconds", scene["duration_seconds"]))
    prompt = (
        f"{scene['video_prompt']} Avoid: {scene.get('negative_prompt', '')} "
        f"--resolution {resolution} --duration {generation_duration} --ratio {project['aspect_ratio']}"
    )
    protocol = str(project.get("video_protocol", "seedance:generations"))
    if protocol == "kling:image2video":
        audio_setting = scene.get("generate_audio", project.get("generate_audio", False))
        sound = "on" if audio_setting is True or str(audio_setting).lower() in {"1", "true", "on", "yes"} else "off"
        payload: dict[str, Any] = {
            "model_name": project["video_model"],
            "image": source_url,
            "prompt": f"{scene['video_prompt']} Avoid: {scene.get('negative_prompt', '')}",
            "duration": str(generation_duration),
            "mode": str(project.get("kling_mode", "pro")),
            "aspect_ratio": project["aspect_ratio"],
            "sound": sound,
        }
    else:
        payload = {
            "model": project["video_model"],
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": source_url}, "role": "first_frame"},
            ],
        }
    job_path = output.with_suffix(output.suffix + ".job.json")
    job_id = None
    if job_path.exists():
        saved_job = load_json(job_path)
        job_id = saved_job.get("id") or saved_job.get("taskId") or saved_job.get("task_id")
    if not job_id:
        submit_path = "/kling/v1/image2video" if protocol == "kling:image2video" else "/ark/v3/generations/tasks"
        job = api_json(submit_path, key, payload)
        job_id = job.get("id") or job.get("taskId") or job.get("task_id")
        if not job_id:
            raise RuntimeError("TokenDance video submission did not include id")
        save_json(job_path, {"id": job_id, "protocol": protocol, "submitted_at": utc_now()})
    if protocol == "kling:image2video":
        url, status = poll_kling_video(key, job_id, timeout)
        usage = {}
        state = (status.get("data") or {}).get("task_status")
    else:
        url, status = poll_video(key, job_id, timeout)
        usage = status.get("usage") or {}
        state = status.get("status")
    with urllib.request.urlopen(url, timeout=120) as response:
        output.write_bytes(response.read())
    save_json(job_path, {"id": job_id, "protocol": protocol, "status": state, "usage": usage, "completed_at": utc_now()})
    return usage


def concat_variant(project: dict[str, Any], root: Path, variant: int, force: bool) -> Path:
    output = root / "output" / f"variant-{variant:02d}.mp4"
    if output.exists() and not force:
        return output
    output.parent.mkdir(parents=True, exist_ok=True)
    variant_scenes = scenes_for_variant(project, variant)
    clips = [task_paths(root, variant, scene["id"])[1] for scene in variant_scenes]
    missing = [str(path) for path in clips if not path.exists()]
    if missing:
        raise RuntimeError(f"cannot assemble variant {variant}; missing clips: {missing}")

    _, _, width, height = dimensions(project)
    fps = int(project.get("fps", 24))
    inputs: list[str] = []
    filters: list[str] = []
    for index, (clip, scene) in enumerate(zip(clips, variant_scenes, strict=True)):
        inputs.extend(["-i", str(clip)])
        duration = float(scene["duration_seconds"])
        filters.append(
            f"[{index}:v]trim=duration={duration},setpts=PTS-STARTPTS,"
            f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={fps},format=yuv420p[v{index}]"
        )
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=index", "-of", "csv=p=0", str(clip)],
            capture_output=True, text=True, timeout=30,
        )
        if probe.returncode == 0 and probe.stdout.strip():
            filters.append(
                f"[{index}:a]atrim=duration={duration},asetpts=PTS-STARTPTS,"
                f"aresample=48000,aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,"
                f"apad=whole_dur={duration}[a{index}]"
            )
        else:
            filters.append(
                f"anullsrc=r=48000:cl=stereo,atrim=duration={duration},"
                f"asetpts=PTS-STARTPTS[a{index}]"
            )
    labels = "".join(f"[v{index}][a{index}]" for index in range(len(clips)))
    filters.append(f"{labels}concat=n={len(clips)}:v=1:a=1[outv][outa]")
    cmd = [
        "ffmpeg", "-y", *inputs, "-filter_complex", ";".join(filters),
        "-map", "[outv]", "-map", "[outa]", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart", str(output),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {result.stderr[-1200:]}")
    return output


def planned_tasks(project: dict[str, Any], root: Path, force: bool) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    for variant in range(1, int(project["variants"]) + 1):
        for scene in scenes_for_variant(project, variant):
            keyframe, clip = task_paths(root, variant, int(scene["id"]))
            tasks.append({
                "variant": variant,
                "scene": int(scene["id"]),
                "keyframe": str(keyframe),
                "clip": str(clip),
                "needs_keyframe": force or not keyframe.exists(),
                "needs_clip": force or not clip.exists(),
            })
    return tasks


def scenes_for_variant(project: dict[str, Any], variant: int) -> list[dict[str, Any]]:
    if "variant_scenes" not in project:
        return project["scenes"]
    for item in project["variant_scenes"]:
        if int(item["variant"]) == int(variant):
            return item["scenes"]
    raise ValueError(f"missing scene plan for variant {variant}")


def scene_for_task(project: dict[str, Any], task: dict[str, Any]) -> dict[str, Any]:
    for scene in scenes_for_variant(project, int(task["variant"])):
        if int(scene["id"]) == int(task["scene"]):
            return scene
    raise ValueError(f"missing scene {task['scene']} for variant {task['variant']}")


def expected_variant_durations(project: dict[str, Any]) -> dict[str, float]:
    return {
        f"variant-{variant:02d}": sum(float(scene["duration_seconds"]) for scene in scenes_for_variant(project, variant))
        for variant in range(1, int(project["variants"]) + 1)
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, help="Project directory containing project.json")
    parser.add_argument("--execute", action="store_true", help="Call paid APIs and write outputs")
    parser.add_argument("--keyframes-only", action="store_true", help="Generate missing keyframes, then stop before video jobs")
    parser.add_argument("--force", action="store_true", help="Regenerate existing paid assets")
    parser.add_argument("--max-workers", type=int, default=2)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--retries", type=int, default=1)
    parser.add_argument("--cost-authorized", action="store_true", help="Confirm that the user authorized paid API calls")
    args = parser.parse_args()

    root = Path(args.project).expanduser().resolve()
    project_path = root / "project.json"
    if not project_path.is_file():
        parser.error(f"missing {project_path}")
    project = load_json(project_path)
    for variant in range(1, int(project["variants"]) + 1):
        for scene in scenes_for_variant(project, variant):
            resolved_references = []
            for value in scene.get("reference_images", []):
                if value.startswith(("http://", "https://", "data:")) or Path(value).is_absolute():
                    resolved_references.append(value)
                else:
                    resolved_references.append(str((root / value).resolve()))
            if resolved_references:
                scene["reference_images"] = resolved_references
    tasks = planned_tasks(project, root, args.force)
    keyframes_needed = sum(task["needs_keyframe"] for task in tasks)
    clips_needed = 0 if args.keyframes_only else sum(task["needs_clip"] for task in tasks)
    generated_seconds = 0
    native_audio_jobs = 0
    for task in tasks:
        if not task["needs_clip"] or args.keyframes_only:
            continue
        scene = scene_for_task(project, task)
        generated_seconds += int(scene.get("generation_duration_seconds", scene["duration_seconds"]))
        audio_setting = scene.get("generate_audio", project.get("generate_audio", False))
        if audio_setting is True or str(audio_setting).lower() in {"1", "true", "on", "yes"}:
            native_audio_jobs += 1
    summary = {
        "mode": "execute" if args.execute else "dry-run",
        "project": str(root),
        "image_model": project["image_model"],
        "video_model": project["video_model"],
        "image_dimensions": f"{project['image_width']}x{project['image_height']}",
        "video_resolution": project.get("video_resolution", "720p"),
        "video_dimensions": f"{project['video_width']}x{project['video_height']}",
        "keyframes_to_generate": keyframes_needed,
        "keyframes_reused": len(tasks) - keyframes_needed,
        "video_jobs_to_generate": clips_needed,
        "video_clips_reused": len(tasks) - clips_needed,
        "paid_video_seconds_to_generate": generated_seconds,
        "native_audio_jobs": native_audio_jobs,
        "retry_ceiling_per_task": args.retries,
        "max_workers": args.max_workers,
        "pricing_status": "not_exposed_by_provider_model_catalog",
        "asset_bank": bool(project.get("asset_bank")),
        "final_videos": 0 if project.get("asset_bank") else project["variants"],
        "expected_duration_seconds_by_variant": expected_variant_durations(project),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if not args.execute:
        return 0
    if not args.cost_authorized:
        print(json.dumps({
            "status": "authorization_required",
            "error": "Paid generation requires --cost-authorized after user approval",
        }, ensure_ascii=False), file=sys.stderr)
        return 2
    if args.max_workers < 1:
        parser.error("max-workers must be positive")
    try:
        api_key = require_api_key()
    except RuntimeError as exc:
        print(json.dumps({"status": "configuration_error", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    status_path = root / "status.json"
    status = load_json(status_path) if status_path.exists() else {"schema_version": 1, "tasks": {}, "costs": []}

    def run_task(task: dict[str, Any]) -> dict[str, Any]:
        keyframe = Path(task["keyframe"])
        clip = Path(task["clip"])
        keyframe.parent.mkdir(parents=True, exist_ok=True)
        clip.parent.mkdir(parents=True, exist_ok=True)
        scene = scene_for_task(project, task)
        attempts = args.retries + 1
        last_error = None
        for attempt in range(1, attempts + 1):
            try:
                if task["needs_keyframe"]:
                    source_url = generate_keyframe(project, scene, task["variant"], keyframe, api_key)
                    task["needs_keyframe"] = False
                else:
                    source_url = None
                usage = None
                if task["needs_clip"] and not args.keyframes_only:
                    usage = generate_clip(project, scene, keyframe, clip, args.timeout, api_key, source_url)
                    task["needs_clip"] = False
                return {**task, "status": "completed", "usage": usage, "completed_at": utc_now()}
            except Exception as exc:  # Preserve partial paid outputs and retry the missing stage.
                last_error = str(exc)
                if attempt < attempts:
                    time.sleep(min(10, 2 * attempt))
        return {**task, "status": "failed", "error": last_error, "completed_at": utc_now()}

    pending = [
        task for task in tasks
        if task["needs_keyframe"] or (task["needs_clip"] and not args.keyframes_only)
    ]
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        futures = {executor.submit(run_task, task): task for task in pending}
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            key = f"v{result['variant']:02d}-s{result['scene']:02d}"
            status["tasks"][key] = result
            if result.get("usage"):
                status.setdefault("usage", []).append({"task": key, **result["usage"]})
            status["updated_at"] = utc_now()
            save_json(status_path, status)
            print(json.dumps({"task": key, "status": result["status"]}, ensure_ascii=False))

    failures = [value for value in status["tasks"].values() if value.get("status") == "failed"]
    if failures:
        print(json.dumps({"status": "partial_failure", "failed_tasks": len(failures)}, ensure_ascii=False))
        return 2

    if args.keyframes_only:
        print(json.dumps({"status": "keyframes_completed", "project": str(root)}, ensure_ascii=False, indent=2))
        return 0

    if project.get("asset_bank"):
        outputs = [
            str(task_paths(root, variant, int(scene["id"]))[1])
            for variant in range(1, int(project["variants"]) + 1)
            for scene in scenes_for_variant(project, variant)
        ]
        status["outputs"] = outputs
        status["updated_at"] = utc_now()
        save_json(status_path, status)
        print(json.dumps({"status": "asset_bank_completed", "outputs": outputs}, ensure_ascii=False, indent=2))
        return 0

    outputs = [str(concat_variant(project, root, variant, args.force)) for variant in range(1, project["variants"] + 1)]
    status["outputs"] = outputs
    status["updated_at"] = utc_now()
    save_json(status_path, status)
    print(json.dumps({"status": "completed", "outputs": outputs}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
