# Analysis schema

Use this schema after deterministic extraction. Do not leave a field as fact when it was inferred.

## Reference breakdown

For every editorial scene, record:

- `start_seconds`, `end_seconds`, `duration_seconds`;
- `shot_size`, `camera`, `setting`, `people`, `product`;
- `visible_action_start`, `visible_action_progress`, `visible_result`;
- `scene_function`: hook, context, product, operation, proof, result, presenter CTA, or end card;
- `top_claim`, `bottom_caption`, `voiceover`, `native_dialogue`, `music`, `sound_effect`;
- `information_density`: number of simultaneously active information layers;
- `certainty` and `evidence`.

## Template DNA

Store reusable structure in `template-dna.json`:

```json
{
  "schema_version": 1,
  "duration_range_seconds": [20, 60],
  "aspect_ratio": "9:16",
  "hook_deadline_seconds": 2,
  "audio_structure": {},
  "scene_functions": [],
  "invariants": [],
  "controlled_variables": [],
  "edit_rules": {},
  "quality_gates": []
}
```

Keep product facts outside template DNA. Template DNA describes communication structure; the product brief describes truth.
