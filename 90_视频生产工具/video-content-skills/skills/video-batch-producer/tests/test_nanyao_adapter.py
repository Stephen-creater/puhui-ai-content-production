#!/usr/bin/env python3
"""Nanyao Grok video adapter contracts."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).parents[1] / "scripts" / "run_pipeline.py"
SPEC = importlib.util.spec_from_file_location("run_pipeline_nanyao", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class NanyaoAdapterTest(unittest.TestCase):
    def test_legacy_seedance_manifest_migrates_to_grok_fast(self) -> None:
        project = {"video_model": "seedance-2.0-mini"}
        self.assertEqual(MODULE.video_model_for_project(project), MODULE.DEFAULT_NANYAO_VIDEO_MODEL)

    def test_legacy_five_second_clip_migrates_to_ten_second_fast_request(self) -> None:
        project = {"video_model": "kling-3.0"}
        scene = {"duration_seconds": 4, "generation_duration_seconds": 5}
        self.assertEqual(MODULE.generation_duration(project, scene), 10)

    def test_fast_generation_defaults_to_longest_duration(self) -> None:
        project = {"video_model": MODULE.DEFAULT_NANYAO_VIDEO_MODEL}
        self.assertEqual(MODULE.generation_duration(project, {"duration_seconds": 4}), 10)

    def test_fast_generation_accepts_only_six_or_ten_seconds(self) -> None:
        project = {"video_model": MODULE.DEFAULT_NANYAO_VIDEO_MODEL}
        self.assertEqual(
            MODULE.generation_duration(project, {"duration_seconds": 4, "generation_duration_seconds": 6}),
            6,
        )
        with self.assertRaisesRegex(ValueError, "must be 6 or 10"):
            MODULE.generation_duration(
                project,
                {"duration_seconds": 4, "generation_duration_seconds": 5},
            )

    def test_poll_uses_completed_response_direct_url(self) -> None:
        direct_url = "https://nanyaovideo.tos-cn-beijing.volces.com/uploads/videos/task-1.mp4"
        with mock.patch.object(
            MODULE,
            "nanyao_api_json",
            return_value={"status": "completed", "progress": 100, "url": direct_url},
        ) as api:
            url, status = MODULE.poll_nanyao_video("secret", "task-1", timeout=1, interval=0)
        self.assertEqual(url, direct_url)
        self.assertEqual(status["progress"], 100)
        api.assert_called_once_with("/v1/videos/task-1", "secret")

    def test_generate_clip_submits_fast_image_reference_and_ten_seconds(self) -> None:
        project = {
            "video_model": MODULE.DEFAULT_NANYAO_VIDEO_MODEL,
            "video_width": 720,
            "video_height": 1280,
        }
        scene = {
            "duration_seconds": 4,
            "video_prompt": "Slow camera push-in.",
            "negative_prompt": "flicker",
        }
        source_url = "https://cdn.example.com/keyframe.png"
        direct_url = "https://nanyaovideo.tos-cn-beijing.volces.com/uploads/videos/task-1.mp4"
        calls: list[tuple[str, dict | None]] = []

        def fake_api(path: str, key: str, payload: dict | None = None, timeout: int = 300) -> dict:
            calls.append((path, payload))
            return {"id": "task-1", "status": "queued"}

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            keyframe = root / "scene.png"
            output = root / "scene.mp4"
            keyframe.touch()
            with (
                mock.patch.object(MODULE, "nanyao_api_json", side_effect=fake_api),
                mock.patch.object(
                    MODULE,
                    "poll_nanyao_video",
                    return_value=(direct_url, {"status": "completed", "progress": 100}),
                ),
                mock.patch.object(MODULE, "download_url", side_effect=lambda url, path: path.write_bytes(b"video")),
            ):
                MODULE.generate_clip(project, scene, keyframe, output, 30, "secret", source_url)

        self.assertEqual(calls[0][0], "/v1/videos")
        self.assertEqual(calls[0][1]["model"], MODULE.DEFAULT_NANYAO_VIDEO_MODEL)
        self.assertEqual(calls[0][1]["duration"], 10)
        self.assertEqual(calls[0][1]["size"], "720x1280")
        self.assertEqual(calls[0][1]["images"], [source_url])


if __name__ == "__main__":
    unittest.main()
