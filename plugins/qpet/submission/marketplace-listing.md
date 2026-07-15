# Marketplace Listing

## Name

Qpet

## Tagline

Turn keywords or a selfie into a distinctive, validated animated chibi pet.

## Short description

Explore three toy-style directions, lock your character's identity, and hatch a polished Codex pet.

## Full description

Qpet turns a short idea, a selfie selected through ChatGPT/Codex's visible camera or photo attachment, or another authorized reference into a 3D-rendered animated pet.

Instead of sending every request through one house style, the plugin first creates three visibly different directions. Each direction varies silhouette, proportions, material, palette, face construction, and accessory logic. Once you choose, it saves a reusable character specification and keeps that identity stable across every animation state.

The production workflow validates transparency and atlas geometry, reviews animation and look directions, repairs only failed states, and packages the result for safe local trial. Selfies remain user-selected inputs; the plugin never activates a camera silently and never includes the source photo in the finished pet.

This creates a 3D-looking 2D sprite pet. It does not create GLB models, add new mouse events, provide cloud synchronization, host permanent download links, or draw live account-usage information on the native Pet surface.

## Distinct value

- three deliberately different concepts, not three recolors
- selfie-to-chibi translation based only on selected visible cues
- deterministic seeds and reusable `pet-spec.json`
- identity locks for face, silhouette, material, palette, and attached props
- targeted row repair instead of complete regeneration
- v2 validation evidence, contact sheets, motion previews, and conflict-aware installation

## Starter prompts

1. Turn “mint astronaut shiba, curious, tiny satchel, soft clay” into three clearly different 3D chibi pet concepts, then let me choose one.
2. Let me take or attach a selfie, then make a Q-version of me that keeps my hair, glasses, and blue hoodie. Show three toy-material directions first.
3. Validate this pet package and tell me exactly which dimensions, transparency, or metadata checks fail.

## Requirements and limitations

- New artwork requires the host's built-in image-generation capability or an authorized existing image.
- Full animation uses the current bundled Codex pet workflow.
- Camera/photo selection is controlled by the host and visibly initiated by the user.
- Local custom pets are not advertised as cloud-synced.
- A public install deep link requires a separate direct HTTPS image host; this skills-only release does not provide one.
- The current Pet renderer has no public plugin HUD slot, so live Usage Remaining as HP is not part of this release.
