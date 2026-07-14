#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
codex_home="${CODEX_HOME:-$HOME/.codex}"
claude_home="${CLAUDE_HOME:-$HOME/.claude}"
start_marker='<!-- loop-engineering:start -->'
end_marker='<!-- loop-engineering:end -->'

install_skill() {
  local home_dir="$1"
  local skill_target="$home_dir/skills/loop-engineering"
  mkdir -p "$home_dir/skills"
  rm -rf "$skill_target"
  cp -R "$repo_dir/loop-engineering" "$skill_target"
  printf 'Installed Skill: %s\n' "$skill_target"
}

update_rule_file() {
  local rule_file="$1"
  local tmp_file
  touch "$rule_file"
  tmp_file="$(mktemp)"
  awk -v start="$start_marker" -v end="$end_marker" '
    $0 == start { skipping = 1; next }
    $0 == end { skipping = 0; next }
    !skipping { print }
  ' "$rule_file" > "$tmp_file"

  while [[ -s "$tmp_file" ]] && [[ "$(tail -c 1 "$tmp_file" | wc -l | tr -d ' ')" == "0" ]]; do
    printf '\n' >> "$tmp_file"
  done
  printf '\n' >> "$tmp_file"
  cat "$repo_dir/codex-global-rule.md" >> "$tmp_file"
  printf '\n' >> "$tmp_file"
  mv "$tmp_file" "$rule_file"
  printf 'Updated global instructions: %s\n' "$rule_file"
}

install_skill "$codex_home"
update_rule_file "$codex_home/AGENTS.md"
install_skill "$claude_home"
update_rule_file "$claude_home/CLAUDE.md"

printf 'Restart Codex and Claude Code, or begin new tasks, to load the changes.\n'
