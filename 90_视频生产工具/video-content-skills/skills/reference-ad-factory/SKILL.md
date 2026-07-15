---
name: reference-ad-factory
description: Orchestrate a complete reference-driven AI short-video factory from real-life hook discovery or authorized finished reference videos and a product truth pack. Use when a user wants to find TikTok UGC hooks under a strict API budget, reproduce the production quality of an existing ad, turn a reference video into one new finished product video, create controlled batches of similar-but-distinct variants, or build a reusable reference-template library without visual workflow tools.
---

# Reference Ad Factory

Run an agent-native pipeline: reference evidence becomes template DNA, product truth becomes constraints, controlled strategies become variants, and generation remains resumable and verifiable.

## Required inputs

- One or more user-owned or authorized reference videos.
- Product brief with verified facts, required action order, prohibited claims, and delivery format.
- Product images; character or brand references when continuity matters.
- Variant count, language, aspect ratio, and cost authority.

## Initialize a project

```bash
python3 scripts/init_project.py \
  --output-root /absolute/path/03_video_projects \
  --project-name product-campaign \
  --reference-video /absolute/path/reference.mp4 \
  --product-image /absolute/path/product-front.png \
  --product-image /absolute/path/product-in-use.png \
  --variants 3 \
  --language en
```

The script copies inputs into a standard local project. Heavy media remains ignored by Git.

## Production workflow

1. When the user lacks a reference or needs real-life opening hooks, use TikHub only as a discovery index. Preview the exact request count and cost before execution:

   ```bash
   python3 scripts/search_tiktok_hooks.py \
     --query "paint spill" \
     --query "renovation dust"
   ```

   Execute only with both hard caps. Every result remains `license_status: unverified`; obtain the creator's permission before downloading, editing, or publishing it commercially.
2. Use `reference-video-analyzer` for every authorized reference. Enrich technical evidence with transcript, on-screen text, shot functions, action progression, information layers, audio structure, and CTA.
3. Derive one `template-dna.json` from structure. When several references exist, preserve patterns supported by multiple examples and label one-off choices.
4. Complete the product brief. Keep product truth independent from template DNA.
5. Create controlled variant plans:

   ```bash
   python3 scripts/plan_variants.py \
     --project /absolute/path/project \
     --variants 5
   ```

6. Write a finished script and shot plan for every variant. Vary the declared strategy; do not rely on model randomness as the only difference.
   Store the authored content in `02_plan/phase2/variant-content.json`, then compile and validate it:

   ```bash
   python3 scripts/compile_variants.py \
     --project /absolute/path/project \
     --check-only
   python3 scripts/compile_variants.py \
     --project /absolute/path/project
   ```

   Compilation rejects missing intake authority, unknown product fact IDs, prohibited phrases, unknown assets, strategy mismatches, and final durations outside 20–60 seconds.
7. Use `video-batch-producer` to generate keyframes first. Review product geometry, identity, hands, action order, and claim accuracy before paid video generation.
8. Generate B-roll and presenter shots. For reliable timing, generate one natural-speed voice file per scene from that scene's exact `spoken_text`; use native model dialogue only for deliberately designed visible speaking shots. Measure voice duration before locking scene windows.
9. Finish captions, top claims, audio, timing, loudness, and delivery encoding with deterministic post-production. Pad short scene voice with tail silence, but never slow narration to fill a scene. Derive captions from the exact TTS input.

   ```bash
   python3 scripts/assemble_variants.py \
     --manifest /absolute/path/project/02_plan/phase2/batch-manifest.json \
     --dry-run
   python3 scripts/assemble_variants.py \
     --manifest /absolute/path/project/02_plan/phase2/batch-manifest.json
   ```
10. Apply [references/quality-gates.md](references/quality-gates.md). Retry only failed assets and retain successful generations.

Read [references/sop.md](references/sop.md) for the complete stage contract. Read [references/variant-strategy.md](references/variant-strategy.md) before producing more than one variant.
Give a cold-start agent or human operator [references/operator-runbook.md](references/operator-runbook.md) for exact commands and stop conditions.

## Non-negotiable rules

- Extract structure from references; do not clone protected branding, exact copy, faces, voices, or frames without permission.
- Lock product facts, geometry, operation order, brand rules, delivery specifications, and prohibited claims.
- Require a paid-generation preview showing job count, model, resolution, estimated duration, and retry policy.
- Keep final duration at least 20 seconds and normally no more than 60 seconds.
- Store scripts, plans, Skills, keyframes, and reports in Git; keep videos, audio, PPT, credentials, signed URLs, and provider metadata local.
- Treat human review as a release gate, not an optional improvement.
