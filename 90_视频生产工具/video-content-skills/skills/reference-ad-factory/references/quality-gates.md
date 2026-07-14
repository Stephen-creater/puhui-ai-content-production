# Quality gates

## Technical

- Final duration is at least 20 seconds and normally at most 60 seconds.
- Resolution, aspect ratio, frame rate, video codec, audio codec, and sample rate match delivery requirements.
- Voice is complete at natural speed, captions remain inside the safe area, and target loudness is met.
- Every scene window is at least as long as its measured voice file; any spare time is tail silence rather than slowed speech.
- Every caption equals the exact `spoken_text` sent to TTS and occupies the same scene window.

## Semantic

- Every claim is supported by the product brief.
- Product structure and action order remain correct in every scene.
- The opening communicates a pain, result, or clear product difference within two seconds.
- The proof sequence visibly demonstrates the promised benefit.
- The CTA is audible, complete, and appropriate for the audience.

## Visual

- Product, presenter, wardrobe, environment, hands, and important props remain continuous.
- Text is added in post, readable, correctly spelled, and not hidden by platform UI.
- No watermark, provider artifact, deformed anatomy, unexplained object change, or product separation appears.

## Batch

- Every variant states its planned difference.
- Differences are meaningful in hook, script, setting, proof, or CTA.
- Batch members do not contradict one another on product facts.
- Failed assets are retried selectively; approved assets are retained.
- A no-reuse batch has one unique keyframe and generated clip per scene, with no paths to an earlier visual bank.
