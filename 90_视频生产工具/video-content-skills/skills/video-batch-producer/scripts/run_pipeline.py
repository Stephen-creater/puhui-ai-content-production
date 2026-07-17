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


TOKENDANCE_GATEWAY = "https://tokendance.space/gateway"
NANYAO_BASE_URL = "https://api.nanyaoai.top"
DEFAULT_NANYAO_VIDEO_MODEL = "grok-imagine-video-1.5-fast"
DEFAULT_NANYAO_FAST_DURATION = 10
NANYAO_FAST_DURATIONS = {6, 10}
NANYAO_FAST_PRICE_CNY = 0.6
PROVIDER_USER_AGENT = "video-content-skills/1.0"


class AmbiguousSubmissionError(RuntimeError):
    """A paid submission may have reached the provider; never retry it blindly."""


def require_key(env_name: str, keychain_service: str) -> str:
    if key := os.environ.get(env_name):
        return key
    result = subprocess.run(
        ["security", "find-generic-password", "-a", getpass.getuser(),
         "-s", keychain_service, "-w"],
        capture_output=True, text=True,
    )
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    raise RuntimeError(
        f"{env_name} is not set and no macOS Keychain item exists for "
        f"service {keychain_service}"
    )


def require_tokendance_api_key() -> str:
    return require_key("TOKENDANCE_API_KEY", "video-content-skills/tokendance")


def require_nanyao_api_key() -> str:
    return require_key("NANYAO_API_KEY", "video-content-skills/nanyao")


def provider_api_json(
    base_url: str,
    provider: str,
    path: str,
    key: str,
    payload: dict[str, Any] | None = None,
    timeout: int = 300,
) -> dict[str, Any]:
    request = urllib.request.Request(
        f"{base_url}{path}",
        data=json.dumps(payload).encode("utf-8") if payload is not None else None,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "User-Agent": PROVIDER_USER_AGENT,
        },
        method="POST" if payload is not None else "GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")[:2000]
        message = f"{provider} HTTP {exc.code} for {path}: {body}"
        if provider == "nanyao" and path == "/v1/videos" and payload is not None and exc.code >= 500:
            raise AmbiguousSubmissionError(message) from exc
        raise RuntimeError(message) from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        message = f"{provider} network error for {path}: {exc}"
        if provider == "nanyao" and path == "/v1/videos" and payload is not None:
            raise AmbiguousSubmissionError(message) from exc
        raise RuntimeError(message) from exc


def tokendance_api_json(
    path: str, key: str, payload: dict[str, Any] | None = None, timeout: int = 300
) -> dict[str, Any]:
    return provider_api_json(TOKENDANCE_GATEWAY, "TokenDance", path, key, payload, timeout)


def nanyao_api_json(
    path: str, key: str, payload: dict[str, Any] | None = None, timeout: int = 300
) -> dict[str, Any]:
    return provider_api_json(NANYAO_BASE_URL, "nanyao", path, key, payload, timeout)


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
    response = tokendance_api_json("/v1/images/generations", key, payload)
    item = response["data"][0]
    source_url = item.get("url")
    if not source_url:
        raise RuntimeError("TokenDance image response did not include data[0].url")
    with urllib.request.urlopen(source_url, timeout=180) as download:
        output.write_bytes(download.read())
    source_path = output.with_suffix(output.suffix + ".source.json")
    save_json(source_path, {"url": source_url, "model": response.get("model", project["image_model"]), "created_at": utc_now()})
    return source_url


def video_model_for_project(project: dict[str, Any]) -> str:
    """Map legacy Seedance/Kling manifests onto the new Grok Fast default."""
    model = str(project.get("video_model", ""))
    return model if model.startswith("grok-imagine-video-") else DEFAULT_NANYAO_VIDEO_MODEL


def generation_duration(project: dict[str, Any], scene: dict[str, Any]) -> int:
    model = video_model_for_project(project)
    declared_model = str(project.get("video_model", ""))
    configured = scene.get(
        "generation_duration_seconds",
        project.get("video_generation_duration_seconds"),
    )
    if declared_model and not declared_model.startswith("grok-imagine-video-"):
        configured = DEFAULT_NANYAO_FAST_DURATION
    if configured is None:
        configured = 15 if model == "grok-imagine-video-1.5-preview" else DEFAULT_NANYAO_FAST_DURATION
    duration = int(configured)
    if model == DEFAULT_NANYAO_VIDEO_MODEL and duration not in NANYAO_FAST_DURATIONS:
        raise ValueError(f"{DEFAULT_NANYAO_VIDEO_MODEL} duration must be 6 or 10, got {duration}")
    if model == "grok-imagine-video-1.5-preview" and duration not in range(1, 16):
        raise ValueError("grok-imagine-video-1.5-preview duration must be 1-15")
    return duration


def poll_nanyao_video(
    key: str, job_id: str, timeout: int, interval: int = 12
) -> tuple[str, dict[str, Any]]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        status = nanyao_api_json(f"/v1/videos/{job_id}", key)
        state = str(status.get("status", "")).lower()
        if state == "completed":
            video_url = status.get("url")
            if not isinstance(video_url, str) or not video_url.startswith(("http://", "https://")):
                raise RuntimeError(f"nanyao video job {job_id} completed without a public top-level url")
            return video_url, status
        if state == "failed":
            raise RuntimeError(f"nanyao video job {job_id} failed: {status.get('error')}")
        time.sleep(interval)
    raise TimeoutError(f"nanyao video job {job_id} did not finish within {timeout}s")


def download_url(url: str, output: Path, timeout: int = 180) -> None:
    """Download a provider result URL without forwarding API credentials."""
    with urllib.request.urlopen(url, timeout=timeout) as response:
        output.write_bytes(response.read())


def generate_clip(
    project: dict[str, Any], scene: dict[str, Any], keyframe: Path, output: Path,
    timeout: int, key: str, source_url: str | None = None,
) -> dict[str, Any]:
    source_path = keyframe.with_suffix(keyframe.suffix + ".source.json")
    if not source_url and source_path.exists():
        source_url = load_json(source_path).get("url")
    if not source_url:
        raise RuntimeError(f"missing source URL metadata for {keyframe}; regenerate its keyframe")
    if not source_url.startswith(("http://", "https://")):
        raise RuntimeError(
            "nanyao requires a public HTTP(S) keyframe URL; regenerate the keyframe "
            "or provide a public reference image URL"
        )
    model = video_model_for_project(project)
    duration = generation_duration(project, scene)
    payload: dict[str, Any] = {
        "model": model,
        "prompt": f"{scene['video_prompt']} Avoid: {scene.get('negative_prompt', '')}",
        "duration": duration,
        "size": f"{int(project['video_width'])}x{int(project['video_height'])}",
    }
    if model == "grok-imagine-video-1.5-preview":
        payload["image"] = source_url
    else:
        payload["images"] = [source_url]
    job_path = output.with_suffix(output.suffix + ".job.json")
    job_id = None
    if job_path.exists():
        saved_job = load_json(job_path)
        if saved_job.get("provider") == "nanyao" and saved_job.get("model") == model:
            job_id = saved_job.get("id")
    if not job_id:
        job = nanyao_api_json("/v1/videos", key, payload)
        job_id = job.get("id")
        if not job_id:
            raise RuntimeError("nanyao video submission did not include id")
        save_json(job_path, {
            "id": job_id,
            "provider": "nanyao",
            "model": model,
            "duration": duration,
            "submitted_at": utc_now(),
        })
    url, status = poll_nanyao_video(key, job_id, timeout)
    download_url(url, output)
    usage = status.get("usage") or {}
    save_json(job_path, {
        "id": job_id,
        "provider": "nanyao",
        "model": model,
        "duration": duration,
        "status": status.get("status"),
        "usage": usage,
        "completed_at": utc_now(),
    })
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


def planned_tasks(
    project: dict[str, Any], root: Path, force: bool,
    force_clips: bool = False, force_keyframes: bool = False,
) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    for variant in range(1, int(project["variants"]) + 1):
        for scene in scenes_for_variant(project, variant):
            keyframe, clip = task_paths(root, variant, int(scene["id"]))
            tasks.append({
                "variant": variant,
                "scene": int(scene["id"]),
                "keyframe": str(keyframe),
                "clip": str(clip),
                "needs_keyframe": force or force_keyframes or not keyframe.exists(),
                "needs_clip": force or force_clips or not clip.exists(),
            })
    return tasks


def task_key(task: dict[str, Any]) -> str:
    return f"v{int(task['variant']):02d}-s{int(task['scene']):02d}"


def filter_tasks(tasks: list[dict[str, Any]], selectors: list[str] | None) -> list[dict[str, Any]]:
    if not selectors:
        return tasks
    requested = list(dict.fromkeys(selectors))
    by_key = {task_key(task): task for task in tasks}
    unknown = [value for value in requested if value not in by_key]
    if unknown:
        raise ValueError(f"unknown task selector: {', '.join(unknown)}")
    return [by_key[value] for value in requested]


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


def validate_paid_caps(
    keyframes_needed: int,
    clips_needed: int,
    generated_seconds: int,
    max_image_jobs: int | None,
    max_video_jobs: int | None,
    max_paid_video_seconds: int | None,
) -> None:
    """Refuse paid work unless explicit numeric ceilings cover the exact delta."""
    checks = (
        ("image jobs", keyframes_needed, max_image_jobs, "--max-image-jobs"),
        ("video jobs", clips_needed, max_video_jobs, "--max-video-jobs"),
        ("paid video seconds", generated_seconds, max_paid_video_seconds, "--max-paid-video-seconds"),
    )
    for label, required, limit, flag in checks:
        if limit is not None and limit < 0:
            raise ValueError(f"{flag} cannot be negative")
        if required > 0 and limit is None:
            raise ValueError(f"paid execution requires {flag}; exact {label} planned: {required}")
        if limit is not None and required > limit:
            raise ValueError(f"planned {label} {required} exceeds {flag}={limit}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, help="Project directory containing project.json")
    parser.add_argument("--execute", action="store_true", help="Call paid APIs and write outputs")
    parser.add_argument("--keyframes-only", action="store_true", help="Generate missing keyframes, then stop before video jobs")
    parser.add_argument("--force", action="store_true", help="Regenerate existing paid assets")
    parser.add_argument("--force-clips", action="store_true", help="Regenerate selected clips while preserving keyframes")
    parser.add_argument("--force-keyframes", action="store_true", help="Regenerate selected keyframes while preserving clips")
    parser.add_argument("--max-workers", type=int, default=2)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--retries", type=int, default=1)
    parser.add_argument("--cost-authorized", action="store_true", help="Confirm that the user authorized paid API calls")
    parser.add_argument("--max-image-jobs", type=int, help="Hard ceiling for paid image jobs in this invocation")
    parser.add_argument("--max-video-jobs", type=int, help="Hard ceiling for paid video jobs in this invocation")
    parser.add_argument("--max-paid-video-seconds", type=int, help="Hard ceiling for paid video seconds in this invocation")
    parser.add_argument(
        "--task", action="append", dest="tasks", metavar="vNN-sNN",
        help="Limit preview or execution to one task; repeat for targeted retries",
    )
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
    if args.force and (args.force_clips or args.force_keyframes):
        parser.error("--force cannot be combined with --force-clips or --force-keyframes")
    try:
        tasks = filter_tasks(
            planned_tasks(project, root, args.force, args.force_clips, args.force_keyframes),
            args.tasks,
        )
    except ValueError as exc:
        parser.error(str(exc))
    keyframes_needed = sum(task["needs_keyframe"] for task in tasks)
    clips_needed = 0 if args.keyframes_only else sum(task["needs_clip"] for task in tasks)
    generated_seconds = 0
    requested_native_audio_jobs = 0
    for task in tasks:
        if not task["needs_clip"] or args.keyframes_only:
            continue
        scene = scene_for_task(project, task)
        generated_seconds += generation_duration(project, scene)
        audio_setting = scene.get("generate_audio", project.get("generate_audio", False))
        if audio_setting is True or str(audio_setting).lower() in {"1", "true", "on", "yes"}:
            requested_native_audio_jobs += 1
    summary = {
        "mode": "execute" if args.execute else "dry-run",
        "project": str(root),
        "image_model": project["image_model"],
        "image_provider": "tokendance",
        "video_provider": "nanyao",
        "video_model": video_model_for_project(project),
        "image_dimensions": f"{project['image_width']}x{project['image_height']}",
        "video_resolution": project.get("video_resolution", "720p"),
        "video_dimensions": f"{project['video_width']}x{project['video_height']}",
        "keyframes_to_generate": keyframes_needed,
        "keyframes_reused": len(tasks) - keyframes_needed,
        "video_jobs_to_generate": clips_needed,
        "video_clips_reused": len(tasks) - clips_needed,
        "paid_video_seconds_to_generate": generated_seconds,
        "paid_caps": {
            "max_image_jobs": args.max_image_jobs,
            "max_video_jobs": args.max_video_jobs,
            "max_paid_video_seconds": args.max_paid_video_seconds,
        },
        "native_audio_jobs": 0,
        "requested_native_audio_jobs": requested_native_audio_jobs,
        "retry_ceiling_per_task": args.retries,
        "max_workers": args.max_workers,
        "selected_tasks": [task_key(task) for task in tasks] if args.tasks else [],
        "pricing_status": "documented_flat_rate_verify_in_console",
        "estimated_video_cost_cny": round(clips_needed * NANYAO_FAST_PRICE_CNY, 2)
        if video_model_for_project(project) == DEFAULT_NANYAO_VIDEO_MODEL else None,
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
    try:
        validate_paid_caps(
            keyframes_needed,
            clips_needed,
            generated_seconds,
            args.max_image_jobs,
            args.max_video_jobs,
            args.max_paid_video_seconds,
        )
    except ValueError as exc:
        print(json.dumps({"status": "cost_cap_required", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    if args.max_workers < 1:
        parser.error("max-workers must be positive")
    try:
        image_api_key = require_tokendance_api_key() if keyframes_needed else None
        video_api_key = require_nanyao_api_key() if clips_needed else None
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
                    assert image_api_key is not None
                    source_url = generate_keyframe(project, scene, task["variant"], keyframe, image_api_key)
                    task["needs_keyframe"] = False
                else:
                    source_url = None
                usage = None
                if task["needs_clip"] and not args.keyframes_only:
                    assert video_api_key is not None
                    usage = generate_clip(project, scene, keyframe, clip, args.timeout, video_api_key, source_url)
                    task["needs_clip"] = False
                return {**task, "status": "completed", "usage": usage, "completed_at": utc_now()}
            except Exception as exc:  # Preserve partial paid outputs and retry the missing stage.
                last_error = str(exc)
                if isinstance(exc, AmbiguousSubmissionError):
                    break
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
