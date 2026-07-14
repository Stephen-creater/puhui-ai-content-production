# Reference-driven short-video SOP

## Stage contract

### 0. Intake

Collect reference videos, product facts, product images, target audience, language, platform, aspect ratio, variant count, deadline, cost authority, required claims, and prohibited claims. Stop when ownership or product truth is unclear.

### 1. Reference evidence

For each reference, produce technical metadata, transcript, scene boundaries, contact sheet, on-screen text, shot functions, action progression, information density, audio roles, hook, proof, payoff, and CTA. Separate measured facts from editorial inference.

### 2. Template DNA

Extract timing ranges, scene functions, information layers, audio architecture, edit rules, and quality gates. Do not place product facts in the template. For multiple references, mark patterns as common, optional, or reference-specific.

### 3. Product truth pack

Record product structure, correct operation, applications, supported claims, forbidden claims, visual invariants, required references, and delivery specification. This file outranks prompts and reference style.

### 4. Variant design

Assign each variant a declared hook strategy and controlled changes. Lock invariants. Generate complete narration, dialogue, top claims, captions, shot durations, keyframe prompts, video prompts, negative prompts, and reference assignments.

Compile authored content with `compile_variants.py` before any paid call. Treat a successful compile as the handoff from editorial planning to deterministic production.

### 5. Cost gate

Show keyframe count, video job count, model, resolution, generated duration, native-audio jobs, retry ceiling, and assets already reusable. Obtain approval unless the user has already authorized cost.

### 6. Keyframes

Generate and review all keyframes before animation. Fail a frame for product geometry, action order, identity drift, hand defects, unsafe text area, misleading claims, or missing proof context.

### 7. Video and sound

Animate approved frames. Keep one main action per generated clip. Use a consistent B-roll voice; reserve native dialogue for visible speakers. Resume missing assets instead of regenerating successful work.

### 8. Post-production

Trim source clips to editorial duration, assemble by shot function, normalize voice, add captions and claims in post, encode delivery media, and generate a contact sheet. Do not depend on the video model for readable text.

### 9. Verification

Run technical checks, transcript checks, visual checks, semantic checks, and a human release review. Save `verify-report.json`, `cost-report.json`, and `provenance.json`.

### 10. Learning loop

Record which hooks, shots, prompts, models, and retries passed. Promote reusable patterns into the template library only after more than one successful delivery.

## Durable project layout

```text
project/
├── 00_input/
│   ├── reference_videos/
│   └── product_images/
├── 01_analysis/
├── 02_plan/
│   └── variants/
├── 03_generation/
├── 04_postproduction/
├── 05_deliverables/
├── 06_reports/
└── 99_tests/
```
