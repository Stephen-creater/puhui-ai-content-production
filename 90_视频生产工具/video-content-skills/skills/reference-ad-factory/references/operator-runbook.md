# Operator runbook

This is the cold-start path for an AI agent or human operator with no conversation context. Replace `REPO` and `PROJECT` once, then execute the gates in order.

```bash
REPO=/absolute/path/to/puhui-ai-content-production
PROJECT="$REPO/03_视频项目/pre-taped-masking-film"
FACTORY="$REPO/90_视频生产工具/video-content-skills/skills/reference-ad-factory"
PRODUCER="$REPO/90_视频生产工具/video-content-skills/skills/video-batch-producer"
```

## Inputs and prerequisites

- Python 3.11+, FFmpeg and ffprobe.
- Reference video under `PROJECT/00_input/reference_videos/`.
- Product reference images and approved product facts.
- TokenDance credential available through the existing environment or macOS Keychain integration.
- Paid generation explicitly authorized by the user.
- Heavy audio and video files are local artifacts and may be Git-ignored.

## Fast path

### 1. Analyze once, reuse by hash

```bash
python3 "$REPO/90_视频生产工具/video-content-skills/skills/reference-video-analyzer/scripts/analyze_reference.py" \
  --input "$PROJECT/00_input/reference_videos/reference-01.mp4" \
  --output-dir "$PROJECT/01_analysis/reference-01"
```

Matching source SHA-256 should return `status: reused`. Do not repeat transcript, OCR or shot extraction when the reference hash is unchanged.

### 2. Compile and validate the five strategies

```bash
python3 "$FACTORY/scripts/compile_variants.py" --project "$PROJECT" --check-only
python3 "$FACTORY/scripts/compile_variants.py" --project "$PROJECT" --force
```

The five strategies must have complete scripts, `spoken_text`, captions, unique visual assets and explicit product-order constraints. Placeholder strategies are a stop condition.

### 3. Generate scene-level voice before locking timing

Generate one Alex / ElevenLabs `eleven_v3` file for every scene, using the exact `spoken_text`. Save each file at its manifest `voiceover_path`.

Measure each audio file with ffprobe. Set that scene's window to at least the measured voice duration plus a short visual margin. Redistribute spare time between scenes while keeping each final video between 20 and 60 seconds.

Hard rules:

- Never slow a full-video voice track to fill the edit.
- Never use `atempo` to lengthen narration.
- Preserve original TTS speed; only pad silence at the tail of a scene.
- Caption text must equal that scene's actual TTS input.

### 4. Preview exact paid delta

```bash
python3 "$PRODUCER/scripts/run_pipeline.py" \
  --project "$PROJECT/03_generation/phase2-v2-unique" \
  --max-workers 4 --retries 1
```

Record new images, new video jobs, generated seconds, resolution, native-audio jobs, retry ceiling and reused assets. Do not execute if any old clip path appears in a no-reuse batch.

### 5. Generate and review keyframes first

```bash
python3 "$PRODUCER/scripts/run_pipeline.py" \
  --project "$PROJECT/03_generation/phase2-v2-unique" \
  --execute --cost-authorized --keyframes-only \
  --max-image-jobs 25 --max-workers 4 --retries 1
```

Review all keyframes. Reject wrong integrated-product geometry, wrong action order, identity drift, bad hands, unsupported claims, embedded text or cross-variant visual reuse. Move only rejected files aside, strengthen their prompts and rerun without `--force`; this regenerates only missing assets.

### 6. Generate and review clips

```bash
python3 "$PRODUCER/scripts/run_pipeline.py" \
  --project "$PROJECT/03_generation/phase2-v2-unique" \
  --execute --cost-authorized \
  --max-image-jobs 0 --max-video-jobs 25 --max-paid-video-seconds 125 \
  --max-workers 4 --retries 1

python3 "$PRODUCER/scripts/verify_project.py" \
  --project "$PROJECT/03_generation/phase2-v2-unique"
```

Review motion in every clip. Reject reversed order, detached tape and film, impossible hand movement, identity changes, frozen output or unintended speech. Retry only failed clips. For example:

```bash
python3 "$PRODUCER/scripts/run_pipeline.py" \
  --project "$PROJECT/03_generation/phase2-v2-unique" \
  --execute --cost-authorized --force-clips \
  --task v01-s02 --task v01-s03 \
  --max-image-jobs 0 --max-video-jobs 2 --max-paid-video-seconds 10 \
  --max-workers 2 --retries 1
```

`--force-clips` preserves approved keyframes and regenerates only the explicitly selected clips. Use `--force-keyframes --keyframes-only` when only selected first frames need replacement; use `--force` only when both stages must be replaced.

### 7. Preview, assemble and verify

```bash
python3 "$FACTORY/scripts/assemble_variants.py" \
  --manifest "$PROJECT/02_plan/phase2-v2/batch-manifest.json" --dry-run

python3 "$FACTORY/scripts/assemble_variants.py" \
  --manifest "$PROJECT/02_plan/phase2-v2/batch-manifest.json" --force
```

Verify all five outputs with ffprobe and human playback. Required release checks:

1. Duration is 20–60 seconds.
2. Voice stays natural from first line to last line.
3. Each subtitle is the exact line spoken in that scene and appears in the same window.
4. The integrated product and tape-first order remain correct.
5. Every variant has its own visual assets; no old keyframe or clip is reused.
6. The hook, pacing and visual information density are not worse than the accepted v2 baseline.

## Failure and resume policy

- Rerun without `--force` to resume only missing paid assets.
- Treat every authorization as single-use for the reviewed dry-run delta. Re-preview and renew approval whenever task count, generated seconds, retry ceiling, model or resolution changes.
- Copy the dry-run numbers into the hard caps. Paid execution is blocked before API-key loading when a required cap is absent or too low.
- Keep successful generations; move rejected outputs into a local review folder instead of deleting the evidence.
- After two text-only failures on product geometry or identity, change the visual anchor/reference strategy before another paid retry.
- Stop on missing authority, unsupported claims, unknown assets, product-order contradictions or a failed release check.
- Commit and push each approved milestone; do not add large generated MP4 files unless the user explicitly requests it.
