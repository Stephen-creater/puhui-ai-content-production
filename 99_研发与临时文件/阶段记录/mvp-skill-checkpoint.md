# Video Skill MVP checkpoint

Updated: 2026-07-14

## Goal

Codex-local Skill: existing script -> scene plan -> batch keyframes -> image-to-video clips -> FFmpeg final videos -> verification.

## Selected upstream reuse

- `togethercomputer/skills` commit `062e98b96a9c836c513f2172ff32bedcc88ebd68`, MIT: `together-images`, `together-video`, keyframe API, polling, downloads, model tables.
- `michaelboeding/skills` commit `84abf02d42612ab0b94a54de1a1a454ae25dd131`, MIT: video producer project manifest, resumable assets, FFmpeg assembly pattern.
- Rejected for this MVP: `browser-use/video-use` is optimized for editing existing footage and requires ElevenLabs; Google Skill needs broader Google/GCS setup.

## Implemented

- Repository: `video-content-skills/`
- Skill: `skills/video-batch-producer/`
- Installed symlink: `~/.codex/skills/video-batch-producer`
- Package: `dist/video-batch-producer.skill`
- Scripts: `plan_project.py`, `run_pipeline.py`, `verify_project.py`
- Defaults: 4 scenes x 5 seconds, 2 variants, 9:16, Seedream 5 Lite keyframes, Seedance 2 Mini video through TokenDance.
- Dry-run is default; `--execute` is required for paid calls.
- Resume skips existing keyframes/clips unless `--force`; submitted video task IDs are persisted before polling.
- API key lookup order: `TOKENDANCE_API_KEY`, then macOS Keychain service `video-content-skills/tokendance`.

## Verification evidence

- Python compile passed for all scripts.
- Skill validator passed.
- Skill packaging passed without `__pycache__`.
- Synthetic smoke project generated two 20-second videos.
- Both outputs verified as H.264, 1080x1920, 24 fps, 20.0 seconds.
- Live TokenDance image call succeeded with Seedream 5 Lite at 1440x2560.
- Live TokenDance Seedance 2 Mini image-to-video call succeeded; response was H.264/AAC, 720x1280, 24 fps, 5.088 seconds.
- Resumable batch smoke project produced two final outputs. Both passed `verify_project.py` as H.264, 720x1280, 24 fps, 5.041667 seconds.
- Representative generated keyframes and middle video frames were visually inspected.
- Secret scan found no pasted API key in the repository or work artifacts.
- Final packaged Skill SHA-256: `2585d25165d97d703dad6601a20ed8d448118ef9cbd49b3bb562fd70b25c8e07`.

## Live provider status

- `ffmpeg` and `ffprobe` are available.
- TokenDance exposes OpenAI Images at `/gateway/v1/images/generations` and Seedance tasks at `/gateway/ark/v3/generations/tasks`.
- The user API key is stored only in macOS Keychain, not the repository.
- Seedream 5 Lite rejected 1024x1024 because it requires at least 3,686,400 pixels; the defaults now satisfy that constraint.
- Seedance completed responses expose `content.video_url`; the live task reported 108,900 completion tokens for a 5-second 720p 9:16 clip.

## Native Codex/ChatCut fallback audit

- Installed ChatCut `video-gen` Skill supports Seedance 2.0 and Kling, including first/last-frame inputs and 4-15 second Seedance clips.
- Installed ChatCut `image-gen` Skill documents a `submit_image` tool for project-native keyframe generation.
- The current ChatCut MCP tool surface exposes `submit_video` and `track_progress` but does not expose `submit_image`; package search finds only documentation references, not an implementation.
- A manual fallback could use Codex image generation plus ChatCut local-media import, but generation consumes credits and requires an exact test script/content direction. Do not spend on placeholder content without approval.
- No environment keys are set for Together, Google/Gemini, OpenAI, Fal, or Replicate.
