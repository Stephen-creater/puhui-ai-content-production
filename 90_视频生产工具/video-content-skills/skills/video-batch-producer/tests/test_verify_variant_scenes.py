#!/usr/bin/env python3
"""Verifier must use the matching variant-specific scene plan."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "verify_project.py"
SPEC = importlib.util.spec_from_file_location("verify_variant_scenes", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class VerifyVariantScenesTest(unittest.TestCase):
    def test_expected_duration_uses_matching_variant(self) -> None:
        project = {
            "variant_scenes": [
                {"variant": 1, "scenes": [{"id": 1, "duration_seconds": 4}]},
                {"variant": 2, "scenes": [{"id": 1, "duration_seconds": 5}]},
            ]
        }
        self.assertEqual(MODULE.expected_duration(project, 1), 4)
        self.assertEqual(MODULE.expected_duration(project, 2), 5)


if __name__ == "__main__":
    unittest.main()
