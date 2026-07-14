#!/usr/bin/env python3
"""Regression tests for natural voice timing and non-reused visuals."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).parents[1] / "scripts" / "assemble_variants.py"
SPEC = importlib.util.spec_from_file_location("assemble_variants_contract", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def valid_manifest() -> dict:
    return {
        "visual_policy": {
            "reuse_existing_clips": False,
            "unique_asset_per_scene": True,
            "required_path_fragment": "03_generation/phase2-v2-unique/",
        },
        "audio_policy": {
            "voice_speed_mode": "natural",
            "caption_source": "spoken_text",
            "min_spoken_wpm": 150,
            "max_spoken_wpm": 260,
        },
        "assets": {
            "v01-s01": "03_generation/phase2-v2-unique/clips/variant-01/scene-01.mp4",
            "v01-s02": "03_generation/phase2-v2-unique/clips/variant-01/scene-02.mp4",
        },
        "variants": [
            {
                "variant_id": "variant-01",
                "duration_seconds": 8.0,
                "scenes": [
                    {
                        "asset": "v01-s01",
                        "duration_seconds": 4.0,
                        "caption": "Painting or sanding?",
                        "spoken_text": "Painting or sanding?",
                        "voiceover_path": "04_postproduction/phase2-v2/voice/variant-01/scene-01.mp3",
                    },
                    {
                        "asset": "v01-s02",
                        "duration_seconds": 4.0,
                        "caption": "Press the yellow tape first.",
                        "spoken_text": "Press the yellow tape first.",
                        "voiceover_path": "04_postproduction/phase2-v2/voice/variant-01/scene-02.mp3",
                    },
                ],
            }
        ],
    }


class NaturalVoiceUniqueVisualsTest(unittest.TestCase):
    def test_accepts_natural_scene_voice_and_unique_visuals(self) -> None:
        result = MODULE.validate_production_contract(valid_manifest())
        self.assertEqual(result["scene_voice_assets"], 2)
        self.assertEqual(result["unique_visual_assets"], 2)

    def test_rejects_caption_that_differs_from_spoken_text(self) -> None:
        manifest = valid_manifest()
        manifest["variants"][0]["scenes"][0]["caption"] = "A different summary."
        with self.assertRaisesRegex(ValueError, "caption must equal spoken_text"):
            MODULE.validate_production_contract(manifest)

    def test_rejects_visual_asset_reuse(self) -> None:
        manifest = valid_manifest()
        manifest["variants"][0]["scenes"][1]["asset"] = "v01-s01"
        with self.assertRaisesRegex(ValueError, "visual asset reused"):
            MODULE.validate_production_contract(manifest)

    def test_rejects_old_visual_bank_paths(self) -> None:
        manifest = valid_manifest()
        manifest["assets"]["v01-s01"] = "03_generation/visual-bank-v1/clips/variant-01/scene-01.mp4"
        with self.assertRaisesRegex(ValueError, "outside required generation root"):
            MODULE.validate_production_contract(manifest)

    def test_scene_voice_filter_never_changes_tempo(self) -> None:
        value = MODULE.scene_voice_filter(7, 4.2)
        self.assertNotIn("atempo", value)
        self.assertIn("apad", value)
        self.assertIn("atrim=duration=4.2", value)

    def test_dry_run_validation_enforces_production_contract(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = MODULE.validate(valid_manifest(), Path(directory), True, True)
        self.assertEqual(result["scene_voice_assets"], 2)
        self.assertEqual(result["unique_visual_assets"], 2)

    def test_rejects_scene_window_shorter_than_natural_voice(self) -> None:
        manifest = valid_manifest()
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            for scene in manifest["variants"][0]["scenes"]:
                voice = project / scene["voiceover_path"]
                voice.parent.mkdir(parents=True, exist_ok=True)
                voice.touch()
            with patch.object(MODULE, "probe_duration", return_value=4.2):
                with self.assertRaisesRegex(ValueError, "voice exceeds scene window"):
                    MODULE.validate(manifest, project, False, True)

    def test_rejects_slow_generated_voice_before_assembly(self) -> None:
        manifest = valid_manifest()
        for scene in manifest["variants"][0]["scenes"]:
            scene["duration_seconds"] = 12.0
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            for scene in manifest["variants"][0]["scenes"]:
                voice = project / scene["voiceover_path"]
                voice.parent.mkdir(parents=True, exist_ok=True)
                voice.touch()
            with patch.object(MODULE, "probe_duration", return_value=10.0):
                with self.assertRaisesRegex(ValueError, "spoken rate outside policy"):
                    MODULE.validate(manifest, project, False, True)


if __name__ == "__main__":
    unittest.main()
