---
name: create-chibi-pet
description: Create a personal 3D chibi desktop pet from a few words, a selfie, or an image the user has permission to use. Use when someone wants to design a Qpet, turn themselves into a chibi character, choose between three different looks, make the chosen character move, or fix an existing pet while keeping its appearance.
---

# Qpet — Create Your 3D Chibi Pet

## Overview

Direct the creative phase that the base pet workflow does not expose: generate three deliberately different 3D chibi concepts, let the user select one, freeze the approved identity in `pet-spec.json`, and then hand production to `$hatch-pet` for animation, QA, packaging, and local installation.

The deliverable is a 3D-rendered 2D sprite pet. Never describe it as a GLB model, real-time 3D scene, custom pointer-event engine, cloud-synced asset, hosted one-click installer, or live account-usage HUD.

## Route the request

- For a new keyword pet, follow the complete workflow.
- For a selfie pet, use the host-provided camera or image attachment, then follow the complete workflow with the photo as an identity reference.
- For concept exploration only, stop after the three concepts or concept board.
- For validation only, read `references/runtime-contract.md` and run `scripts/validate_pet_package.py`.
- For repair, preserve the existing `pet-spec.json`, identify the failed animation row, and pass only that row to `$hatch-pet`'s repair workflow.
- For real-time 3D, GLB, physics, collision, or new mouse behavior, state the boundary and offer a 3D-rendered animated sprite pet instead.
- For a request to show Usage Remaining as live HP on the pet, read `references/usage-hp.md`, explain the current host boundary, and do not query account data or install a background monitor from this marketplace skill.

## 1. Check the runtime

Before image work or packaging, call `load_workspace_dependencies` once for the task and reuse the result. Use the returned Python executable for scripts that need Pillow. From this skill directory, run:

```bash
python3 scripts/check_runtime.py --pretty
```

Continue when both `$imagegen` and `$hatch-pet` are installed. If `$hatch-pet` is missing, keep the concept/spec outputs and tell the user to open **Settings → Pets → Create your own pet** once, then retry. Do not download replacement code or request an API key.

## 2. Capture the brief or selfie

For keyword input, require only one useful keyword and infer the remaining choices. Useful inputs include creature or object archetype, personality, occupation, material, palette, and one signature accessory. Do not block on missing optional fields. Treat every explicit user cue as a literal design constraint: never turn a requested species, role, color, material, or accessory into an unrelated badge or generic prop.

For a selfie request:

1. Explain that the plugin uses ChatGPT/Codex's own camera or attachment control; a Skills-only plugin has no direct camera API and must not activate the camera silently.
2. Ask the user to tap the camera/photo attachment when the host shows it, or upload an existing image. On hosts without a camera action, use the normal image attachment flow.
3. Treat the user's act of selecting or capturing that image for this request as consent to transform it. Do not inspect the photo library or any unrelated image.
4. Preserve recognizable, non-sensitive visual cues such as hair silhouette/color, face shape, glasses, facial hair, clothing colors, and a chosen accessory. Do not identify the person or infer ethnicity, health, religion, sexuality, politics, exact age, or other sensitive traits.
5. Keep the result clearly stylized and original. Never package the source selfie inside the pet.

If the image includes another person, ask the user to confirm they are authorized to transform that person's likeness. For a named brand without a concrete brief, use `$hatch-pet`'s brand-discovery route later. For a copyrighted character, logo, official mascot, or living-artist imitation, create an original alternative using only high-level traits and never claim affiliation.

Create a working directory inside the current project, for example `pet-runs/<safe-pet-id>/`. Never interpolate raw user text into a path or shell command.

## 3. Generate three art directions

Run the deterministic concept generator. Pass repeated or comma-separated keywords, map an explicit material/style phrase to `--material`, and use `--language auto` unless the user asks for a specific output language:

```bash
python3 scripts/chibi_pet_spec.py \
  --keywords "mint-green astronaut shiba, curious, tiny attached satchel" \
  --name "Mint Orbit" \
  --material "soft clay" \
  --language auto \
  --format both \
  --json-out /absolute/path/to/pet-runs/mint-orbit/pet-spec.json \
  --markdown-out /absolute/path/to/pet-runs/mint-orbit/concepts.md
```

For a selfie, add neutral descriptors derived only from visible non-sensitive features to `--keywords`, pass `--source-mode selfie`, and add at most eight visible cues with repeated `--likeness-cue` flags. Keep the actual image attached as the authoritative likeness reference rather than trying to encode identity in text:

```bash
python3 scripts/chibi_pet_spec.py \
  --keywords "cheerful creative, blue hoodie" \
  --source-mode selfie \
  --likeness-cue "short side-parted black hair" \
  --likeness-cue "round dark glasses" \
  --language auto \
  --format both \
  --json-out /absolute/path/to/pet-runs/chibi-me/pet-spec.json \
  --markdown-out /absolute/path/to/pet-runs/chibi-me/concepts.md
```

Read `references/design-system.md`. Present all three directions with silhouette, proportions, material, face language, palette strategy, and accessory logic. The directions must differ on at least four axes; changing only color does not count. Before showing them, audit every concept against the full user brief. All concepts must visibly preserve the required subject/species, role, personality, primary color, material family, and accessory type. If one loses a hard constraint, correct the brief before previewing it.

When visual previews are requested or would help selection, use `$imagegen` to create one three-panel concept board from the generated brief. Attach the selfie or other authorized reference to the image request. Keep the same person or semantic core across panels while honoring each direction's separate construction. Use a neutral studio background for concept selection; do not make sprites yet. Do not use logos, readable text, scenery, or named-artist imitation.

Ask the user to choose A, B, or C. If the user said “surprise me”, is unavailable, or explicitly requested autonomous completion, choose `recommended_concept_id` from the deterministic output and record that decision.

## 4. Lock the approved identity

The generator's top-level identity lock remains pending during exploration. After the user chooses, copy the selected concept's complete `candidate_identity` into an `approved_identity_lock` in `pet-spec.json`; do not combine heads, faces, materials, or props from different directions. The approved lock must state:

- silhouette and head-to-body ratio
- face construction and original eye design
- material and surface response
- primary, secondary, and accent colors
- markings and asymmetry
- accessory geometry, attachment, and handedness
- elements that must never appear

For selfie pets, also record a short `likeness_lock` containing only visible cues necessary for continuity. Do not store identity claims, biometric measurements, or sensitive inferences. After approval, variations may change pose and expression only. Do not silently change species, proportions, face, material, palette, or props.

## 5. Hatch the pet

Apply the installed `$hatch-pet` skill for all visual production, deterministic assembly, direction QA, repair, packaging, and installation. Give it:

- the selected concept and identity lock from `pet-spec.json`
- `style-preset=3d-toy`, `clay`, `plush`, or the closest approved non-pixel preset
- the approved concept image and every identity-defining authorized reference
- a stable description calling for a compact whole-body 3D-rendered chibi sprite

Do not recreate `$hatch-pet`'s atlas pipeline locally and do not generate a complete atlas in one image request. Require its full v2 gates: nine standard animation rows, four cardinal anchors, sixteen look directions, transparency cleanup, contact sheets, motion previews, blind direction QA, validation, and `spriteVersionNumber: 2` packaging. When the installed workflow can safely process independent animation rows concurrently, let it do so with the same approved identity lock; never skip a row or QA gate to save time.

Keep the user's visible progress list aligned to:

1. Preparing the three concepts.
2. Locking the chosen look.
3. Building and checking the animations.
4. Packaging the pet for trial.

## 6. Validate and install safely

Read `references/runtime-contract.md` before export. Validate the staged package with the bundled Python returned by `load_workspace_dependencies`:

```bash
"$PYTHON" scripts/validate_pet_package.py /absolute/path/to/pet-package --pretty
```

Never overwrite or delete an existing local pet silently. If the destination id exists, show the conflict and require explicit confirmation. A local Skills-only plugin may install into the supported desktop pet directory after confirmation; it must not promise cloud sync or a permanent HTTPS download.

Build a deep link only when the final image already has a public, direct, unauthenticated HTTPS URL with no redirect:

```bash
python3 scripts/build_install_deeplink.py \
  --name "Mint Orbit" \
  --image-url "https://cdn.example.com/mint-orbit.webp" \
  --description "A curious mint astronaut shiba." \
  --sprite-version 2
```

Do not invent or upload to a hosting URL. Without hosting, report the local package path and the in-app installation result. After a selfie run, tell the user where any working copy of the source photo remains and offer to remove that copy; do not delete the user's original attachment or photo-library item.

## Completion criteria

For a full request, finish only when these artifacts exist and pass review:

- selected concept and `pet-spec.json`
- transparent v2 spritesheet and `pet.json`
- deterministic validation report
- contact sheet and motion previews
- direction QA evidence
- local package path, plus installation status when authorized

For concept-only, validation-only, or repair-only requests, report the narrower requested result without claiming a complete pet.
