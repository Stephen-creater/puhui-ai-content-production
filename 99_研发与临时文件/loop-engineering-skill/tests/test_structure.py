#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "loop-engineering" / "SKILL.md"
RULE = ROOT / "codex-global-rule.md"
INSTALLER = ROOT / "install.sh"


def require(text: str, fragment: str, source: Path) -> None:
    assert fragment in text, f"{source}: missing {fragment!r}"


skill = SKILL.read_text(encoding="utf-8")
rule = RULE.read_text(encoding="utf-8")
installer = INSTALLER.read_text(encoding="utf-8")

frontmatter = re.match(r"\A---\n(.*?)\n---\n", skill, re.DOTALL)
assert frontmatter, "SKILL.md must start with YAML frontmatter"
frontmatter_keys = {
    line.split(":", 1)[0]
    for line in frontmatter.group(1).splitlines()
    if ":" in line
}
assert frontmatter_keys == {"name", "description"}, frontmatter_keys

for field in ("Purpose", "End state", "Boundaries", "Authority"):
    require(skill, field, SKILL)

for contract in (
    "Ask exactly one question",
    "proceed immediately without waiting for confirmation",
    "Treat plans as hypotheses, not commands",
    "Claim completion only when the observable end state has been verified",
    "Design the storage contract before substantial file creation",
    "Keep the project root scannable",
    "Prefer relative paths inside project manifests",
    "do not silently normalize it as a side effect",
):
    require(skill, contract, SKILL)

require(rule, "use the `loop-engineering` Skill before acting", RULE)
require(rule, "trivial questions", RULE)
require(rule, "establish or reuse a storage contract", RULE)
require(rule, "third-party repositories", RULE)
require(installer, "loop-engineering:start", INSTALLER)
require(installer, "loop-engineering:end", INSTALLER)
require(installer, "CLAUDE_HOME", INSTALLER)
require(installer, "CLAUDE.md", INSTALLER)
require(installer, "AGENTS.md", INSTALLER)

print("loop-engineering structure and behavior contract: PASS")
