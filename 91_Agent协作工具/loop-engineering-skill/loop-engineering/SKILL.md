---
name: loop-engineering
description: Establish commander intent, design a clean project storage contract before substantial file creation, then let the agent autonomously close the execution loop. Use for implementation, modification, publishing, consequential decisions, multi-step work, long-running tasks, or any task expected to create several files, folders, repositories, generated assets, or intermediate artifacts. Ask one high-value clarification at a time only when needed; otherwise restate the intent briefly and proceed.
---

# Loop Engineering

Control the intent, not the action sequence.

## Apply the intent gate

Use this gate for substantive collaboration: work that executes or changes something, publishes externally, makes a consequential decision, or requires multiple steps or a sustained loop.

Skip the gate for trivial transformations, simple factual questions, one-line commands, and similarly low-consequence requests unless ambiguity would materially change the answer.

Before acting, determine whether the request provides enough of these four fields:

1. **Purpose** — Why do this, and what reality should change?
2. **End state** — What observable conditions define success? Include essential key tasks only when they are outcomes that must be true, not prescribed motions.
3. **Boundaries** — What must not be changed, exposed, spent, degraded, or sacrificed?
4. **Authority** — Which means may the agent choose autonomously, and which decisions or external effects require escalation?

Use available context and safe read-only inspection before asking the user for information that can be discovered directly.

## Design the storage contract before substantial file creation

Before creating a new project directory, cloning a repository, or producing several related files, inspect the current workspace and decide where each artifact class belongs. Do this before the first substantial write, not after the workspace becomes cluttered.

Prefer an existing project convention when one is present. Otherwise establish the smallest useful storage contract and state it briefly when it affects the user. A typical contract distinguishes:

- `inputs/` or `sources/` for user-provided and immutable source material;
- `src/`, `skills/`, or another domain-standard path for maintained code and reusable tools;
- `projects/` or clearly named project folders for active business deliverables;
- `output/` or `deliverables/` for final artifacts intended for review or handoff;
- `work/`, `tmp/`, or `.scratch/` for disposable intermediates, smoke tests, renders, caches, and checkpoints;
- `research/` or a workspace-external location for third-party repositories and reference implementations.

Adapt names to the existing ecosystem; separation of lifecycle is mandatory, exact folder names are not.

Apply these safeguards:

1. Keep the project root scannable. Do not place loose generated artifacts at the root when a clear category exists.
2. Keep maintained source, business inputs, final deliverables, and disposable work separate.
3. Do not clone unrelated or third-party repositories inside a business deliverable tree unless the user explicitly wants vendoring. Preserve each repository boundary.
4. Use descriptive, stable names. Add dates or versions where they disambiguate; do not rely on names such as `final`, `new`, `test`, or `work2` alone.
5. Keep generated and reproducible artifacts out of source folders. Record regeneration commands or provenance when future reuse matters.
6. Prefer relative paths inside project manifests. If an absolute path is unavoidable, document it and update references whenever files move.
7. Reuse an existing scratch directory and checkpoint instead of creating a new top-level folder for every experiment.
8. Before cleanup or reorganization, inspect references, symlinks, manifests, Git boundaries, and user-owned files. Never delete merely because an artifact appears temporary.

For a long task, keep a compact checkpoint in the designated scratch area containing the intent, verified state, important paths, and next action. Do not duplicate large logs or source material in the checkpoint.

If the task begins in an already disorganized workspace, do not silently normalize it as a side effect. Continue safely within a contained work area, then propose or perform reorganization only when authorized.

## Resolve ambiguity

Treat the intent as clear enough when a capable agent can choose among reasonable methods, recognize completion, and avoid unacceptable tradeoffs without guessing at a material preference.

If a material gap remains:

1. Continue any safe, useful, read-only discovery that can reduce uncertainty.
2. Ask exactly one question: the unresolved question with the highest effect on direction, acceptance, or safety.
3. Prefer concrete alternatives when they make the tradeoff easier to answer.
4. Repeat on later turns only while material ambiguity remains.

Do not ask the user to fill a fixed template. Do not re-ask facts already supplied. Do not seek precision that would not change execution. Do not turn clarification into ceremonial approval.

## State the commander intent

When the intent is clear, briefly restate it and proceed immediately without waiting for confirmation:

```text
Intent: [purpose]
Done when: [observable end state]
Boundaries: [hard constraints]
Authority: [agent discretion and escalation points]
```

Compress or omit fields that are obvious. For small but substantive work, one sentence is enough.

## Run the loop

Operate autonomously inside the agreed intent:

1. Inspect the current reality and shared context.
2. Establish or reuse the storage contract before substantial file creation.
3. Select the next action most likely to advance the end state.
4. Act within the boundaries and delegated authority.
5. Verify the actual effect against observable evidence.
6. Adapt and repeat until the end state is reached or a genuine blocker requires the user.

Treat plans as hypotheses, not commands. When reality invalidates a planned method, change the method while preserving the intent. Report material deviations and newly discovered risks concisely; do not stop merely because the original plan became obsolete.

Exercise disciplined initiative: take reasonable, reversible, in-scope actions without asking the user to micromanage them. Escalate when a choice would alter the purpose, relax a boundary, accept a materially different risk, or create an external effect outside the delegated authority.

## Close the loop

Claim completion only when the observable end state has been verified. If completion is impossible, report:

- the unmet end-state condition;
- the evidence for the blocker;
- the smallest decision or external change needed to continue.

Higher-priority instructions and safety requirements always remain boundaries, even when the user does not restate them.

For contrasting examples, read [references/examples.md](references/examples.md).
