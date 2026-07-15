#!/usr/bin/env python3
"""Tests for the budget-gated TikHub real-footage search helper."""

from __future__ import annotations

import importlib.util
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).parents[1] / "scripts" / "search_tiktok_hooks.py"
SPEC = importlib.util.spec_from_file_location("search_tiktok_hooks", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class SearchTikTokHooksTest(unittest.TestCase):
    def test_dry_run_does_not_load_credential_or_call_network(self) -> None:
        with mock.patch.object(MODULE, "resolve_api_key") as key, mock.patch.object(MODULE, "request_json") as request:
            output = io.StringIO()
            with redirect_stdout(output):
                result = MODULE.main(["--query", "paint spill", "--query", "renovation dust"])
        self.assertEqual(result, 0)
        self.assertIn('"estimated_cost_usd": 0.002', output.getvalue())
        key.assert_not_called()
        request.assert_not_called()

    def test_execute_requires_both_hard_caps_before_key_loading(self) -> None:
        with mock.patch.object(MODULE, "resolve_api_key") as key:
            with self.assertRaisesRegex(SystemExit, "max-requests"):
                MODULE.main(["--query", "paint spill", "--execute", "--cost-authorized"])
        key.assert_not_called()

    def test_extracts_only_safe_metadata_and_marks_license_unverified(self) -> None:
        payload = {
            "data": {
                "search_item_list": [
                    {
                        "aweme_info": {
                            "aweme_id": "123",
                            "desc": "Paint spill",
                            "create_time": 42,
                            "author": {"unique_id": "painter"},
                            "statistics": {"play_count": 1000, "digg_count": 50},
                            "video": {"duration": 8500, "play_addr": {"url_list": ["signed-secret-url"]}},
                        }
                    }
                ]
            }
        }
        result = MODULE.extract_candidates(payload, "paint spill")
        self.assertEqual(result[0]["source_url"], "https://www.tiktok.com/@painter/video/123")
        self.assertEqual(result[0]["duration_seconds"], 8.5)
        self.assertEqual(result[0]["license_status"], "unverified")
        self.assertNotIn("play_addr", result[0])

    def test_execute_deduplicates_and_writes_outputs(self) -> None:
        payload = {
            "code": 0,
            "data": {
                "search_item_list": [
                    {
                        "aweme_info": {
                            "aweme_id": "123",
                            "desc": "Dust everywhere",
                            "author": {"unique_id": "builder"},
                            "statistics": {"play_count": 20, "digg_count": 2},
                            "video": {"duration": 7000},
                        }
                    }
                ]
            },
        }
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(
            MODULE, "resolve_api_key", return_value="hidden"
        ), mock.patch.object(MODULE, "request_json", return_value=payload) as request:
            result = MODULE.main(
                [
                    "--query",
                    "renovation dust",
                    "--query",
                    "renovation dust",
                    "--output-dir",
                    directory,
                    "--execute",
                    "--cost-authorized",
                    "--max-requests",
                    "1",
                    "--max-cost-usd",
                    "0.001",
                ]
            )
            self.assertEqual(result, 0)
            self.assertTrue((Path(directory) / "candidates.json").is_file())
            self.assertTrue((Path(directory) / "candidates.md").is_file())
            self.assertEqual(request.call_count, 1)


if __name__ == "__main__":
    unittest.main()
