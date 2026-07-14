# Third-party notices

## Together AI agent Skills

- Source: https://github.com/togethercomputer/skills
- Commit inspected: `062e98b96a9c836c513f2172ff32bedcc88ebd68`
- License: MIT, Copyright (c) 2025 Together AI
- Reused concepts: image generation with base64 output; image-to-video `frame_images`; asynchronous polling; signed-output download; model capability tables.

## Michael Boeding agent Skills

- Source: https://github.com/michaelboeding/skills
- Commit inspected: `84abf02d42612ab0b94a54de1a1a454ae25dd131`
- License: MIT, Copyright (c) 2025
- Reused concepts: durable `project.json`; per-scene folders; resumable intermediate assets; FFmpeg normalization and concatenation.

Both upstream licenses permit use, modification, and redistribution when their copyright and license notices are retained. This file records provenance; generated media remains subject to the selected model provider's terms and the user's source-asset rights.

## TokenDance adapter

- Service documentation: https://tokendance.space/docs/multi-protocol
- Model catalogue/API: https://tokendance.space/models and `/gateway/v1/models`
- Reused code: none. The adapter is an original standard-library HTTP implementation.
- Data flow: prompts and generated keyframes are sent to TokenDance, which routes them
  to the selected image/video model provider. API keys are read from environment or
  macOS Keychain and are never written to project files.
