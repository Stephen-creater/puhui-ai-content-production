#!/usr/bin/env python3
"""Verify the repository storage contract and local Markdown links."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable


TOOL_ROOT = Path(__file__).resolve().parent
REPO_ROOT = TOOL_ROOT.parents[1]
CONTRACT_PATH = TOOL_ROOT / "repository-contract.json"
MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def load_contract(path: Path = CONTRACT_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def is_excluded(path: Path, root: Path, excludes: Iterable[str]) -> bool:
    relative = path.relative_to(root).as_posix()
    return any(relative == item or relative.startswith(f"{item}/") for item in excludes)


def tracked_files(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"], cwd=root, check=True, capture_output=True, text=True
    )
    return [line for line in result.stdout.splitlines() if line]


def check_repository(root: Path, contract: dict, tracked: Iterable[str] = ()) -> list[str]:
    errors: list[str] = []
    required_roots = contract["required_roots"]
    scratch = contract["canonical_local_scratch"]

    for relative in required_roots:
        if not (root / relative).is_dir():
            errors.append(f"missing required root directory: {relative}")

    for relative in contract["forbidden_duplicate_paths"]:
        if (root / relative).exists():
            errors.append(f"forbidden duplicate path exists: {relative}")

    readme = root / "README.md"
    if not readme.is_file():
        errors.append("missing root README.md")
    else:
        readme_text = readme.read_text(encoding="utf-8")
        for relative in [*required_roots, scratch]:
            if f"`{relative}`" not in readme_text:
                errors.append(f"root README does not document: {relative}")

    allowed_entries = {
        *required_roots,
        scratch,
        *contract["allowed_root_files"],
        ".git",
        ".DS_Store",
    }
    for entry in root.iterdir():
        if entry.name not in allowed_entries:
            errors.append(f"unexpected root entry: {entry.name}")

    excludes = contract["readme_scan_excludes"]
    for markdown in root.rglob("README.md"):
        if is_excluded(markdown, root, excludes):
            continue
        text = markdown.read_text(encoding="utf-8")
        for target in MARKDOWN_LINK.findall(text):
            clean_target = target.split("#", 1)[0].strip()
            if not clean_target or clean_target.startswith(("http://", "https://", "mailto:")):
                continue
            resolved = (markdown.parent / clean_target).resolve()
            if not resolved.exists():
                errors.append(
                    f"broken README link: {markdown.relative_to(root)} -> {target}"
                )

    for relative in tracked:
        if Path(relative).name == ".DS_Store":
            errors.append(f"tracked Finder metadata: {relative}")

    return sorted(set(errors))


def main() -> int:
    contract = load_contract()
    errors = check_repository(REPO_ROOT, contract, tracked_files(REPO_ROOT))
    if errors:
        print("repository hygiene: FAIL", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("repository hygiene: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
