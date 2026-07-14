# Operator runbook

This runbook is for a new AI agent or a human operator with no prior conversation context.

## Prerequisites

- Python 3.11+, FFmpeg, ffprobe, and the three local Skills are available.
- The project contains `intake.json`, `product-brief.json`, `template-dna.json`, `production-plan.json`, and `variant-content.json`.
- Heavy media exists locally even though Git ignores it.
- TokenDance credentials are stored in the environment or macOS Keychain.

## Commands

1. Analyze or reuse the reference:

   ```bash
   python3 reference-video-analyzer/scripts/analyze_reference.py \
     --input PROJECT/00_input/reference_videos/reference-01.mp4 \
     --output-dir PROJECT/01_analysis/reference-01
   ```

   Matching source hashes return `status: reused` without regenerating files.

2. Validate and compile editorial content:

   ```bash
   python3 reference-ad-factory/scripts/compile_variants.py --project PROJECT --check-only
   python3 reference-ad-factory/scripts/compile_variants.py --project PROJECT --force
   ```

3. Preview paid delta work:

   ```bash
   python3 video-batch-producer/scripts/run_pipeline.py \
     --project PROJECT/03_generation/phase2-hooks \
     --max-workers 2 --retries 1
   ```

   Record image count, video jobs, generated video seconds, native-audio jobs, resolution, reuse counts, retry ceiling, and provider pricing availability.

4. Generate keyframes only after cost authorization:

   ```bash
   python3 video-batch-producer/scripts/run_pipeline.py \
     --project PROJECT/03_generation/phase2-hooks \
     --execute --cost-authorized --keyframes-only --max-workers 2 --retries 1
   ```

5. Review every keyframe. Reject wrong product geometry, action order, identity, hands, claims, or text. Continue only when all pass.

6. Generate missing clips:

   ```bash
   python3 video-batch-producer/scripts/run_pipeline.py \
     --project PROJECT/03_generation/phase2-hooks \
     --execute --cost-authorized --max-workers 2 --retries 1
   ```

7. Generate one complete Alex / ElevenLabs `eleven_v3` voiceover per variant. Save files at the exact `voiceover_path` values in `batch-manifest.json`. A human may use the ChatCut voice interface; an agent may use the ChatCut voice Skill after user authorization.

8. Preview and assemble:

   ```bash
   python3 reference-ad-factory/scripts/assemble_variants.py \
     --manifest PROJECT/02_plan/phase2/batch-manifest.json --dry-run
   python3 reference-ad-factory/scripts/assemble_variants.py \
     --manifest PROJECT/02_plan/phase2/batch-manifest.json --force
   ```

9. Verify hook clips, final videos, transcript, captions, product truth, and human release approval. Do not call a batch release-ready without the human gate.

## Failure policy

- Re-run without `--force` to resume only missing paid assets.
- Never delete successful generations during retry.
- After two prompt-only failures on identity or geometry, strengthen the visual anchor instead of submitting a third text-only retry.
- Stop on missing authority, unsupported claims, unknown assets, or product-order contradictions.
