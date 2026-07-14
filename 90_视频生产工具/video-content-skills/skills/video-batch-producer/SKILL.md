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
- `TOKENDANCE_API_KEY` only when executing paid generation. On macOS, the runner
  also reads Keychain service `video-content-skills/tokendance` for the current user.

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
     --execute --keyframes-only --max-workers 1
   ```

   Inspect every keyframe. Do not submit video jobs until product structure, character
   continuity, hand anatomy, and action order pass visual review.

5. Show the user the planned counts: keyframes, video jobs, variants, model names, and script-derived expected final duration. Reject plans under 20 seconds. Flag plans over 60 seconds and explain why the script needs the extra time. Obtain approval before paid generation unless the user already explicitly authorized execution and cost.

6. Execute the complete pipeline:

   ```bash
   python3 scripts/run_pipeline.py \
     --project /absolute/path/work/project-name \
     --execute \
     --max-workers 2
   ```

7. Verify all deliverables:

   ```bash
   python3 scripts/verify_project.py --project /absolute/path/work/project-name
   ```

8. Open representative keyframes and final videos for visual review. Machine verification is not proof of semantic or visual quality.

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

Never delete successful generations during retry. Re-running with `--execute` resumes missing assets only. Use `--force` only when the user explicitly wants to pay to regenerate existing assets.

## Provider and model selection

The default provider is TokenDance (`tokendance.space`), using its OpenAI-compatible
image endpoint and Ark-compatible Seedance asynchronous video endpoint behind one API key.

- Default image model: `seedream-5.0-lite`
- Default video model: `seedance-2.0-mini`
- Default vertical dimensions: keyframes `1440x2560`, video `720x1280`
- Default scene source duration: `5` seconds. Final edited shot lengths may be shorter.
- Default final-duration band: `20–60` seconds, determined by the script rather than a fixed runtime.

Read [references/models.md](references/models.md) before changing a model. Validate keyframe and dimension support rather than assuming compatibility.

For higher-quality final ads, set `video_model` to `seedance-2.0` and
`video_resolution` to `1080p`. If Seedance rejects an AI-generated presenter frame with
`InputImageSensitiveContentDetected.PrivacyInformation`, switch the project to
`video_model: kling-3.0` and `video_protocol: kling:image2video`; preserve completed clips.

For Kling 3.0 dialogue shots, set scene-level `generate_audio: true` and put the
speaker plus exact short dialogue in `video_prompt`. Keep each spoken generation within
3–15 seconds. Use native dialogue for visible speaking shots; use one consistent
voiceover track in post for B-roll when cross-scene voice continuity matters.

## Safety and quality gates

- Never print or store API keys in the project.
- Treat API generation as paid and network-mutating.
- Send only prompts and generated keyframes to TokenDance and its routed model provider.
- Use only assets the user owns or is permitted to process.
- Reject misleading product claims, unauthorized face/voice cloning, and copyrighted source reuse without permission.
- Require human review for product shape, text, hands/faces, continuity, branding, and factual accuracy.

## Implementation provenance

The original provider flow was adapted from the MIT-licensed official
`togethercomputer/skills` repository; the active TokenDance adapter uses only Python's
standard library. The project-manifest and FFmpeg assembly approach is adapted from the
MIT-licensed `michaelboeding/skills` video producer. Read
[references/THIRD_PARTY_NOTICES.md](references/THIRD_PARTY_NOTICES.md) for provenance.
