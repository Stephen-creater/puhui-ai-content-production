# Phase 2 cold-start audit

## Result

A sub-agent with no conversation context could locate the three Skills, inspect the baseline, verify the reference and model availability, and run safe previews. It could not reach five executable variants before this phase because the strategy plan stopped at `script_required` and the paid preview omitted parts of the cost contract.

## Measured read-only steps

| Step | Time |
|---|---:|
| Python / FFmpeg / ffprobe availability | 0.06s |
| Each CLI `--help` | 0.02–0.05s |
| Existing plan validation refusal | 0.02s |
| Existing analysis reuse refusal before cache fix | 0.05s |
| Producer preview | 0.04–0.08s |
| Final-video ffprobe | 0.04s |
| TokenDance model catalog | 0.11s |

## Blocking findings and implemented response

- P0: strategy placeholders did not compile into scripts, shot plans, or executable manifests. Added `compile_variants.py`, structured intake and product truth, five authored variant plans, and `batch-manifest.json`.
- P0: cost preview lacked resolution, generated seconds, native audio jobs, retry ceiling, and reuse counts. Added these fields and explicit `--cost-authorized` execution.
- P1: dry-run created directories. Separated path calculation from directory creation and added check-only modes where production decisions are verified.
- P1: internal paths were not consistently portable. Relative reference-image paths now resolve from the producer project root.
- P1: repeat analysis wasted work. Matching reference SHA-256 now reuses the prior analysis; measured reuse time is about 0.03s.
- P2: operator steps were implicit. Added a command-level runbook with failure and retry policy.

## Remaining intentional human gates

- Transcript/OCR and editorial meaning still require an AI or trained operator.
- Product truth must be approved before claims compile.
- Keyframes and final videos require visual review.
- ChatCut TTS can be run by an agent or manually in the UI; generated audio must use the exact manifest paths.
