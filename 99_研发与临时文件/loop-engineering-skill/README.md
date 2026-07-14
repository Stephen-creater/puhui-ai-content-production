# Loop Engineering Skill

A Codex/agent skill for replacing action-level micromanagement with clear commander intent and autonomous, verified execution loops.

It turns substantive requests into four control surfaces:

- **Purpose:** why the work matters and what reality should change
- **End state:** observable conditions that define completion
- **Boundaries:** what cannot be touched or sacrificed
- **Authority:** which means the agent may choose and when it must escalate

If a material field is missing, the agent asks one high-value question at a time. If the intent is already executable, it briefly restates the intent and starts immediately. It may change a failed plan, but never the underlying intent or boundaries.

## Install for Codex

```bash
git clone https://github.com/Stephen-creater/loop-engineering-skill.git
cd loop-engineering-skill
./install.sh
```

The installer copies the Skill to `${CODEX_HOME:-~/.codex}/skills/loop-engineering` and adds a marked trigger rule to `${CODEX_HOME:-~/.codex}/AGENTS.md`. Existing content is preserved, and repeated installation updates the Skill without duplicating the rule.

Restart Codex or begin a new task after installation so the updated Skill catalog and global instructions are loaded.

## Repository layout

```text
loop-engineering/          # distributable Skill source
codex-global-rule.md       # global trigger block installed into AGENTS.md
tests/test_structure.py    # structure and behavior-contract checks
install.sh                 # idempotent local installer
```

## Verify

```bash
python3 tests/test_structure.py
```

## Origin

The design distills loop engineering and mission-command ideas into a practical human-agent collaboration contract: centralize intent, decentralize means, verify effects, and preserve disciplined initiative when the original plan stops fitting reality.

## License

MIT
