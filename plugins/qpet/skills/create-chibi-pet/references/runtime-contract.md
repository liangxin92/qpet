# Pet Runtime Contract

Use this reference for export, validation, installation, and market claims.

## Product boundary

The pet is a transparent animated 2D atlas rendered with a 3D chibi appearance. It does not add a real-time 3D model, physics engine, collision system, new mouse events, or a custom native state machine.

The Skills-only plugin has no documented direct camera API. Camera capture and photo selection remain host-controlled, visible user actions. When a camera action is unavailable, request a normal image attachment. Never use shell commands, AppleScript, browser automation, or hidden media APIs to activate a camera.

## Current desktop v2 package

The current bundled desktop workflow expects:

- PNG or WebP
- `1536×2288`
- 8 columns × 11 rows
- `192×208` per cell
- transparent background
- `pet.json` with `spriteVersionNumber: 2`
- unused cells fully transparent

Rows 0–8 are idle, running-right, running-left, waving, jumping, failed, waiting, running, and review. Rows 9–10 contain sixteen clockwise look directions in 22.5-degree steps. Treat this as a versioned current-client contract, not a permanent public API; rely on the installed `$hatch-pet` skill as the production authority.

## Public web upload

The public web uploader documents a transparent PNG/WebP at `1536×1872`, no larger than 20 MiB. This is a separate 8×9 v1 export. Do not upload or label a `1536×2288` v2 atlas as a web v1 asset.

## Deep links

Pet install links use this shape:

```text
codex://pets/install?name=<name>&imageUrl=<absolute-https-url>&description=<optional>&spriteVersionNumber=2
```

Only build the link when `imageUrl` is a direct public HTTPS image URL. Do not use localhost, cookies, authentication, redirects, an HTML download page, or an invented URL. A Skills-only plugin has no built-in hosting service.

## Local installation and portrait safety

- Validate before installing.
- Sanitize ids and keep output inside intended run/package directories.
- Detect an existing pet id before writing.
- Require explicit confirmation before replacement.
- Never read secrets or request an API key for the built-in image workflow.
- Never promise cloud sync; custom pets are local assets unless the host explicitly says otherwise.
- Process only the photo the user deliberately selected for this request.
- Never add the selfie to the final pet package, marketplace test data, logs, or screenshots.
- Disclose any retained working copy and offer deletion after successful packaging.
