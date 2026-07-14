# TokenDance MVP model choices

Current model availability must be checked at `https://tokendance.space/gateway/v1/models`.

## Images

| Use | Model | Notes |
|---|---|---|
| Default keyframes | `seedream-5.0-lite` | OpenAI Images compatible; minimum 3,686,400 pixels |
| Higher-fidelity keyframes | `seedream-5.0-pro` | Ark image protocol; confirm parameters before switching |

Validated dimensions are `1440x2560` for 9:16, `2560x1440` for 16:9, and
`2048x2048` for 1:1. The endpoint may return JPEG bytes even when the local filename
uses `.png`; downstream FFmpeg detects content rather than relying on the suffix.

## Videos

| Model | Duration | Useful dimensions | Keyframes |
|---|---:|---|---|
| `seedance-2.0-mini` | 5s validated | 720p, 9:16 validated | First, first+last, references |
| `seedance-2.0-fast` | Provider dependent | 720p documented | First, first+last, references |
| `kling-3.0` | 3–15s described | 16:9, 9:16, 1:1 | First and optional last |
| `happyhorse-1.0-i2v` | 3–15s described | 720p/1080p | First |

The default Seedance submission endpoint is `/gateway/ark/v3/generations/tasks`; poll
the same path with `/{task_id}`. Completed responses expose `content.video_url`.
Kling image-to-video uses `/gateway/kling/v1/image2video`; poll with `/{task_id}` and
read `data.task_result.videos[0].url`. In live testing, Kling 3.0 accepted the same
AI-generated realistic presenter frames that Seedance rejected as possible real-person
privacy content. Treat this as provider behavior, not proof of future policy stability.
Do not change only the model name. Check protocol, duration, dimensions, keyframe roles,
audio behavior, and current pricing first.
