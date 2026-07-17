#!/usr/bin/env python3
"""Variant-specific prompts must remain distinct throughout paid generation."""

from __future__ import annotations

import importlib.util
import hashlib
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "run_pipeline.py"
SPEC = importlib.util.spec_from_file_location("run_pipeline_variant_scenes", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


PROJECT = {
    "variants": 2,
    "variant_scenes": [
        {
            "variant": 1,
            "scenes": [
                {"id": 1, "duration_seconds": 4, "keyframe_prompt": "unique kitchen hook", "video_prompt": "move left"}
            ],
        },
        {
            "variant": 2,
            "scenes": [
                {"id": 1, "duration_seconds": 5, "keyframe_prompt": "unique bathroom hook", "video_prompt": "move right"}
            ],
        },
    ],
}


class VariantSpecificScenesTest(unittest.TestCase):
    def test_returns_the_scene_plan_for_each_variant(self) -> None:
        self.assertEqual(MODULE.scenes_for_variant(PROJECT, 1)[0]["keyframe_prompt"], "unique kitchen hook")
        self.assertEqual(MODULE.scenes_for_variant(PROJECT, 2)[0]["keyframe_prompt"], "unique bathroom hook")

    def test_planned_tasks_keep_both_variant_scene_pairs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            tasks = MODULE.planned_tasks(PROJECT, Path(directory), False)
        self.assertEqual([(item["variant"], item["scene"]) for item in tasks], [(1, 1), (2, 1)])

    def test_rejects_a_missing_variant_scene_plan(self) -> None:
        broken = {**PROJECT, "variants": 3}
        with self.assertRaisesRegex(ValueError, "missing scene plan for variant 3"):
            MODULE.scenes_for_variant(broken, 3)

    def test_task_lookup_uses_variant_and_scene_together(self) -> None:
        scene = MODULE.scene_for_task(PROJECT, {"variant": 2, "scene": 1})
        self.assertEqual(scene["video_prompt"], "move right")

    def test_reports_duration_for_every_variant(self) -> None:
        self.assertEqual(MODULE.expected_variant_durations(PROJECT), {"variant-01": 4, "variant-02": 5})

    def test_filters_paid_work_to_explicit_retry_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            tasks = MODULE.planned_tasks(PROJECT, Path(directory), True)
        selected = MODULE.filter_tasks(tasks, ["v02-s01"])
        self.assertEqual([(item["variant"], item["scene"]) for item in selected], [(2, 1)])

    def test_rejects_unknown_retry_task(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            tasks = MODULE.planned_tasks(PROJECT, Path(directory), True)
        with self.assertRaisesRegex(ValueError, "unknown task selector"):
            MODULE.filter_tasks(tasks, ["v09-s09"])

    def test_clip_only_retry_preserves_approved_keyframe(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            keyframe, clip = MODULE.task_paths(root, 1, 1, create=True)
            keyframe.touch()
            clip.touch()
            tasks = MODULE.planned_tasks(PROJECT, root, False, force_clips=True)
        task = tasks[0]
        self.assertFalse(task["needs_keyframe"])
        self.assertTrue(task["needs_clip"])

    def test_paid_caps_require_numeric_ceiling_for_each_nonzero_stage(self) -> None:
        with self.assertRaisesRegex(ValueError, "--max-video-jobs"):
            MODULE.validate_paid_caps(0, 2, 10, 0, None, 10)

    def test_paid_caps_reject_over_budget_plan(self) -> None:
        with self.assertRaisesRegex(ValueError, "exceeds --max-paid-video-seconds=9"):
            MODULE.validate_paid_caps(1, 2, 10, 1, 2, 9)

    def test_paid_caps_accept_exact_authorized_delta(self) -> None:
        MODULE.validate_paid_caps(1, 2, 10, 1, 2, 10)

    def test_video_generation_requires_keyframe_review_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            keyframe, _ = MODULE.task_paths(root, 1, 1, create=True)
            keyframe.write_bytes(b"approved image")
            task = MODULE.planned_tasks(PROJECT, root, False)[0]
            with self.assertRaisesRegex(ValueError, "missing keyframe-review.json"):
                MODULE.validate_keyframe_reviews(root, [task])

    def test_keyframe_review_is_bound_to_current_image_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            keyframe, _ = MODULE.task_paths(root, 1, 1, create=True)
            keyframe.write_bytes(b"approved image")
            review = {
                "reviews": {
                    "v01-s01": {
                        "approved": True,
                        "image_sha256": hashlib.sha256(b"approved image").hexdigest(),
                        "checks": {name: True for name in MODULE.KEYFRAME_REVIEW_CRITERIA},
                    }
                }
            }
            (root / "keyframe-review.json").write_text(json.dumps(review), encoding="utf-8")
            task = MODULE.planned_tasks(PROJECT, root, False)[0]
            MODULE.validate_keyframe_reviews(root, [task])
            keyframe.write_bytes(b"changed after review")
            with self.assertRaisesRegex(ValueError, "changed after review"):
                MODULE.validate_keyframe_reviews(root, [task])

    def test_combined_keyframe_and_video_run_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            tasks = MODULE.planned_tasks(PROJECT, Path(directory), False)
            with self.assertRaisesRegex(ValueError, "--keyframes-only"):
                MODULE.validate_keyframe_reviews(Path(directory), tasks)


if __name__ == "__main__":
    unittest.main()
