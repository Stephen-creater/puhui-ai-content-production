---
name: video-batch-producer
description: Convert an existing script into multiple finished short videos by automatically planning scenes, generating a keyframe for every scene, animating each keyframe with a video model, resuming failed jobs, concatenating clips, and verifying outputs. Use for script-to-video, batch product videos, keyframe-to-video pipelines, or a minimal automated AI video production loop. Do not use for editing long existing footage or for scriptwriting from an undefined topic.
---

# Video Batch Producer

Turn a finished script into batch short-video outputs. Keep the workflow agent-native: use the project manifest and scripts instead of building a visual workflow.

## Required inputs

- A UTF-8 script file or explicit script text.
- Desired number of output variants. Default to `2`.
- Aspect ratio. Default to `9:16`.
- Final duration follows the finished script. Enforce at least `20` seconds; target
  `20–60` seconds for normal short-form delivery. Do not force every video to 20
  seconds. Exceed 60 seconds only when the script's information or user direction
  clearly requires it, and state the reason in the plan.
- `TOKENDANCE_API_KEY` for paid keyframe generation and `NANYAO_API_KEY` for paid
  video generation. On macOS, the runner also reads Keychain services
  `video-content-skills/tokendance` and `video-content-skills/nanyao`.

## Workflow

1. Create a project and deterministic first-pass scene plan:

   ```bash
   python3 scripts/plan_project.py \
     --script /absolute/path/script.txt \
     --output /absolute/path/work/project-name \
     --variants 2 \
     --scenes 4
   ```

2. Read `project.json`. Improve `keyframe_prompt` and `video_prompt` using the script's actual meaning. Preserve the JSON schema. Do not invent product claims. Add absolute local paths or URLs under a scene's optional `reference_images` array when product, character, or style references exist.
   For two or more outputs, use `variant_scenes`; every generated clip must have its
   own `keyframe_prompt`, `video_prompt`, and `variation_dimensions`. Record all seven
   fields: `object_type`, `object_form`, `environment`, `coverage_state`, `shot_scale`,
   `camera_motion`, and `person_or_work_state`. The runner rejects repeated prompts,
   missing fields, and duplicate seven-field combinations before loading any API key.
   When the model's minimum generation length exceeds the edited shot length, keep
   `duration_seconds` as the final timeline duration and add
   `generation_duration_seconds` for the paid model request. Concatenation trims each
   source clip to `duration_seconds` automatically.

3. Inspect the full cost-bearing plan without calling an API:

   ```bash
   python3 scripts/run_pipeline.py --project /absolute/path/work/project-name
   ```

4. Generate keyframes first when product geometry, human identity, or operation order matters:

   ```bash
   python3 scripts/run_pipeline.py \
     --project /absolute/path/work/project-name \
     --execute --cost-authorized --keyframes-only \
     --max-image-jobs 8 --max-workers 1
   ```

   Inspect every keyframe at full resolution. For protective-film products, reject any
   hole, tear, split, missing coverage, detached tape edge, tape longer than the film,
   or film that does not connect continuously to the full lower edge of the tape.
   Record each decision before submitting video jobs:

   ```bash
   python3 scripts/review_keyframe.py \
     --project /absolute/path/work/project-name \
     --task v01-s01 --approve \
     --notes "One intact sheet; full coverage; tape and film connected edge-to-edge"
   ```

   Use `--reject` for a failed image, regenerate only that keyframe, inspect it again,
   then record a new decision. The review stores the image SHA-256. Video generation
   is blocked if any review is missing, rejected, incomplete, or refers to an older
   version of the image.

5. Show the user the planned counts: keyframes, video jobs, variants, model names, and script-derived expected final duration. Reject plans under 20 seconds. Flag plans over 60 seconds and explain why the script needs the extra time. Obtain approval before paid generation unless the user already explicitly authorized execution and cost.

6. Execute the complete pipeline:

   ```bash
   python3 scripts/run_pipeline.py \
     --project /absolute/path/work/project-name \
     --execute --cost-authorized \
     --max-image-jobs 0 --max-video-jobs 8 --max-paid-video-seconds 80 \
     --max-workers 2
   ```

7. Verify all deliverables:

   ```bash
   python3 scripts/verify_project.py --project /absolute/path/work/project-name
   ```

8. Open representative keyframes and final videos for visual review. Machine verification is not proof of semantic or visual quality.

For a shared hook, CTA, or reusable shot bank rather than a standalone final video,
set `"asset_bank": true` in `project.json`. The runner generates and verifies the
individual clips but skips final concatenation and the 20-second final-video rule.
Only use asset-bank mode when another manifest explicitly consumes those clips.

## Output contract

The project directory is the durable checkpoint:

```text
project-name/
├── project.json
├── status.json
├── keyframes/variant-01/scene-01.png
├── clips/variant-01/scene-01.mp4
├── output/variant-01.mp4
└── verify-report.json
```

Never delete successful generations during retry. Re-running with `--execute` resumes missing assets only. Use repeated `--task vNN-sNN` selectors with `--force-clips` to regenerate only rejected clips while preserving approved keyframes. Use `--force-keyframes --keyframes-only` for rejected first frames. Use `--force` only when the user explicitly wants to pay to regenerate both stages.

## Provider and model selection

The pipeline deliberately separates providers: TokenDance generates keyframes and
nanyao (`api.nanyaoai.top`) generates Grok video clips.

- Default image model: `seedream-5.0-lite`
- Default video model: `grok-imagine-video-1.5-fast`
- Default vertical dimensions: keyframes `1440x2560`, video `720x1280`
- Default paid source duration: `10` seconds, the longest Fast duration. Final edited
  shot lengths remain independent and concatenation trims each source clip to
  `duration_seconds`.
- Default final-duration band: `20–60` seconds, determined by the script rather than a fixed runtime.

Read [references/models.md](references/models.md) before changing a model. Validate keyframe and dimension support rather than assuming compatibility.

Fast accepts only `6` or `10` seconds. Override `generation_duration_seconds` only
when a six-second source is intentional. Preview accepts `1–15` seconds but exactly
one public reference image and is not the production default. Nanyao's supplied API
document does not promise controlled native dialogue, so use the established Alex
voiceover and subtitle post-production path for deterministic speech.

## Safety and quality gates

- Never print or store API keys in the project.
- Treat API generation as paid and network-mutating.
- Every paid invocation requires numeric ceilings for each nonzero stage: `--max-image-jobs`, `--max-video-jobs`, and `--max-paid-video-seconds`. Copy the exact dry-run counts; the runner refuses missing or exceeded caps before loading the API key.
- Authorization applies to one reviewed delta only. Dry-run again and obtain renewed approval before expanding task selectors, retry count, model, resolution, or generated seconds.
- Send image prompts and references only to TokenDance; send video prompts and public
  generated-keyframe URLs only to nanyao. Nanyao rejects base64, local, and private URLs.
- A paid nanyao submission that times out or returns HTTP 5xx is ambiguous. Do not
  resubmit blindly; inspect the provider task log first.
- Use only assets the user owns or is permitted to process.
- Reject misleading product claims, unauthorized face/voice cloning, and copyrighted source reuse without permission.
- Require human review for product shape, text, hands/faces, continuity, branding, and factual accuracy.
- Keyframe review is a hard code gate, not a prose reminder. Generate and review
  keyframes in a separate invocation; a combined keyframe-plus-video paid run is refused.

## Implementation provenance

The original provider flow was adapted from the MIT-licensed official
`togethercomputer/skills` repository; the active TokenDance image adapter and nanyao
video adapter use only Python's standard library. The project-manifest and FFmpeg assembly approach is adapted from the
MIT-licensed `michaelboeding/skills` video producer. Read
[references/THIRD_PARTY_NOTICES.md](references/THIRD_PARTY_NOTICES.md) for provenance.
