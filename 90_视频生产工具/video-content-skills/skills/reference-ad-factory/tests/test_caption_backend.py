#!/usr/bin/env python3
"""Regression tests for caption rendering on FFmpeg builds without libass."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

from PIL import Image


SCRIPT = Path(__file__).parents[1] / "scripts" / "assemble_variants.py"
SPEC = importlib.util.spec_from_file_location("assemble_variants", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class CaptionBackendTest(unittest.TestCase):
    def test_falls_back_to_png_overlay_without_ass_filter(self) -> None:
        self.assertEqual(MODULE.select_caption_backend({"overlay", "scale"}), "png-overlay")

    def test_caption_png_has_transparent_canvas_and_visible_text(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "caption.png"
            MODULE.write_caption_png(output, "WORK FASTER", "Press tape first, then pull film.", 1080, 1920)
            image = Image.open(output)
            self.assertEqual(image.mode, "RGBA")
            self.assertEqual(image.size, (1080, 1920))
            alpha = image.getchannel("A")
            self.assertEqual(alpha.getpixel((0, 0)), 0)
            self.assertGreater(alpha.getbbox()[3] - alpha.getbbox()[1], 100)


if __name__ == "__main__":
    unittest.main()
