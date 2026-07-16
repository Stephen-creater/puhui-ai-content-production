from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "check_repository.py"
SPEC = importlib.util.spec_from_file_location("check_repository", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


CONTRACT = {
    "required_roots": ["01_inputs", "91_tools"],
    "canonical_local_scratch": "work",
    "forbidden_duplicate_paths": ["91_tools/work"],
    "allowed_root_files": ["README.md", "AGENTS.md"],
    "readme_scan_excludes": ["work"],
}


class RepositoryHygieneTest(unittest.TestCase):
    def make_valid_root(self, directory: str) -> Path:
        root = Path(directory)
        for relative in ["01_inputs", "91_tools", "work"]:
            (root / relative).mkdir()
        (root / "AGENTS.md").write_text("rules\n", encoding="utf-8")
        (root / "README.md").write_text(
            "`01_inputs` `91_tools` `work`\n", encoding="utf-8"
        )
        return root

    def test_accepts_repository_matching_contract(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.make_valid_root(directory)
            self.assertEqual(MODULE.check_repository(root, CONTRACT), [])

    def test_reports_missing_root_and_broken_readme_link(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.make_valid_root(directory)
            (root / "01_inputs").rmdir()
            (root / "README.md").write_text(
                "`01_inputs` `91_tools` `work` [missing](missing.md)\n",
                encoding="utf-8",
            )
            errors = MODULE.check_repository(root, CONTRACT)
            self.assertIn("missing required root directory: 01_inputs", errors)
            self.assertTrue(any("broken README link" in error for error in errors))

    def test_rejects_duplicate_work_area(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.make_valid_root(directory)
            (root / "91_tools/work").mkdir()
            errors = MODULE.check_repository(root, CONTRACT)
            self.assertIn("forbidden duplicate path exists: 91_tools/work", errors)


if __name__ == "__main__":
    unittest.main()
