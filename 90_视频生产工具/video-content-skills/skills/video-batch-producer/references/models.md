# Production model choices

Provider capabilities and prices may change. Check the live TokenDance model list for
images and the nanyao console for Grok video before authorizing a paid batch.

## Images: TokenDance

| Use | Model | Notes |
|---|---|---|
| Default keyframes | `seedream-5.0-lite` | OpenAI Images compatible; minimum 3,686,400 pixels |
| Higher-fidelity keyframes | `seedream-5.0-pro` | Ark image protocol; confirm parameters before switching |

Validated dimensions are `1440x2560` for 9:16, `2560x1440` for 16:9, and
`2048x2048` for 1:1. The endpoint may return JPEG bytes even when the local filename
uses `.png`; downstream FFmpeg detects content rather than relying on the suffix.

## Videos: nanyao Grok

| Model | Duration | Input | Production status |
|---|---:|---|---|
| `grok-imagine-video-1.5-fast` | exactly 6s or 10s | text-only or multiple public image URLs | default; 10s |
| `grok-imagine-video-1.5-preview` | any integer 1–15s | exactly one public image URL | optional; not default |

The Fast adapter posts to `POST /v1/videos`, polls `GET /v1/videos/{id}` every
12 seconds, and downloads the completed response's top-level `url` directly. Do not
call `/v1/videos/{id}/content`: the updated provider document replaced that path with
a direct object-storage URL. The URL needs no API key and is retained for about three
days, so download it promptly.

Reference images must be publicly reachable HTTP(S) URLs. Base64/data URLs, local
paths, localhost, private IPs, and intranet URLs are rejected. The TokenDance keyframe
response URL is recorded beside each generated image and used as the nanyao source.
Regenerate the keyframe if that public URL has expired.

Fast is documented at CNY 0.6 per job for both 6 and 10 seconds. The runner therefore
defaults to 10 seconds and trims each clip to the final `duration_seconds` during
assembly. Treat this price as a planning estimate and verify the console before paid
execution. The supplied nanyao API document does not guarantee controlled native
dialogue; retain the separate voiceover/subtitle post-production path.
