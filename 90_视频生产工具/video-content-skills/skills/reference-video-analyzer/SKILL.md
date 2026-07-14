---
name: reference-video-analyzer
description: Analyze an existing short reference video into technical metadata, scene boundaries, contact sheets, transcript evidence, shot functions, information layers, pacing, audio structure, and reusable template DNA. Use when a user supplies a finished ad or social video and wants to reproduce its quality, extract its production pattern, compare it with another video, or use it as the structural input for AI video generation.
---

# Reference Video Analyzer

Convert a user-owned or authorized reference video into evidence and a reusable structural template. Extract structure; do not copy protected frames, branding, or exact wording into the new ad.

## Workflow

1. Run deterministic media analysis:

   ```bash
   python3 scripts/analyze_reference.py \
     --input /absolute/path/reference.mp4 \
     --output-dir /absolute/path/project/01_analysis/reference-01
   ```

   Add `--transcript-file /absolute/path/transcript.txt` when a transcript already exists.

2. Use a transcription Skill for speech and a visual-capable agent for on-screen text. Do not use local speech recognition unless the user permits it.

3. Read `reference-analysis.json` and inspect `contact-sheet-auto.jpg`. Review the original video around every detected boundary; automated scene detection is evidence, not final editorial truth.

4. Enrich the analysis using [references/analysis-schema.md](references/analysis-schema.md):

   - assign one function to each scene;
   - record visible action progression;
   - separate top claims, captions, voiceover, presenter dialogue, music, and effects;
   - mark the hook deadline, proof sequence, payoff, and CTA;
   - identify invariants versus reusable variables.

5. Produce `template-dna.json`. Preserve timing ranges and scene functions rather than copying surface content.

## Quality gates

- Keep technical facts traceable to ffprobe or measured frames.
- Mark uncertain transcription, OCR, identity, product claims, and scene boundaries.
- Describe what each shot accomplishes, not only what appears in it.
- Treat model-generated or burned-in text as unreliable until visually checked.
- Reject face or voice cloning without permission.
- Analyze videos only when the user owns them or is authorized to process them.

## Output contract

```text
reference-01/
├── reference-analysis.json
├── contact-sheet-auto.jpg
├── transcript.txt              # optional
├── reference-breakdown.md      # agent-enriched
└── template-dna.json            # agent-enriched
```

The deterministic script creates the first two files. The agent creates the enriched files after visual and transcript review.
