#!/usr/bin/env python3
"""Variant-specific prompts must remain distinct throughout paid generation."""

from __future__ import annotations

import importlib.util
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


if __name__ == "__main__":
    unittest.main()
