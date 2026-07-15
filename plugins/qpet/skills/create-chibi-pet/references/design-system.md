# 3D Chibi Design System

Use this reference during concept generation and identity locking.

## Difference gate

Every concept must preserve the user's semantic core while changing at least four of these axes:

1. silhouette family
2. head-to-body ratio and limb proportions
3. material and surface response
4. face construction and eye language
5. palette structure, not merely hue
6. accessory shape and attachment
7. energy and pose language

Reject three concepts that read as recolors of one template.

User constraints are not variation axes. A requested species/archetype, role, personality, primary color, material family, and attached accessory must remain legible in every concept. Vary how those constraints are constructed, not whether they exist. For example, a required satchel can be an oversized cross-body vinyl bag, an integrated soft-clay side pouch, or a compact resin hard-shell module, but it must remain an attached satchel in all three.

## Direction families

Use these as starting families, then adapt them to the keywords:

- **A — Iconic collectible:** one bold outer contour, 1.6–2.0:1 head-to-body ratio, glossy vinyl or resin, simplified facial planes, one oversized signature accessory, controlled two-color palette with one accent.
- **B — Tactile storybook:** rounder or pear-shaped body, 1.3–1.6:1 ratio, soft clay or flocked surface, pressed or inset facial details, handcrafted asymmetry, warmer split-complementary palette, accessory integrated into the silhouette.
- **C — Kinetic mini hero:** compact wedge or bean silhouette, 1.2–1.5:1 ratio, mixed matte and translucent materials, more directional brows/ears/antennae, higher-contrast palette, small functional prop with a clear attachment point.

The generator may choose other families when the keywords call for them, but the difference gate remains mandatory.

When the user specifies a primary color, preserve that color in every direction while changing palette structure: dominant-color ratio, secondary hue family, accent contrast, translucent versus opaque use, and where the color appears. Do not replace a required mint-green subject with a random palette.

## Selfie translation

Preserve likeness through a small set of visible, non-sensitive cues:

- hair mass, part, length, and color
- face silhouette and cheek/jaw softness
- glasses shape, facial hair, and other visible accessories
- clothing color blocks selected by the user
- one expression cue, such as calm, bright, focused, or mischievous

Exaggerate only after choosing the invariant cues. Avoid photoreal skin texture, biometric measurements, identity matching, and sensitive-attribute inference. Keep all three concepts recognizably based on the same authorized photo while varying their toy construction.

## Pet-safe geometry

- Keep the whole body readable inside a `192×208` cell.
- Prefer large identity cues over tiny decoration.
- Keep every prop physically attached; avoid loose particles, floor shadows, glow, text, and scenery.
- Avoid thin connectors, open loops, tiny fingers, dense hair strands, and chroma-key-adjacent colors that make extraction fragile.
- Make asymmetry intentional and record which screen side owns it.
- Preserve the same construction across all states and look directions.

## Identity-lock template

Record the following for the selected concept:

```json
{
  "silhouette": "",
  "proportions": {"head_to_body": "", "limbs": ""},
  "face": {"construction": "", "eyes": "", "mouth": ""},
  "material": {"primary": "", "finish": "", "secondary": ""},
  "palette": {"primary": "", "secondary": "", "accent": ""},
  "markings": [],
  "accessory": {"shape": "", "attachment": "", "side": ""},
  "likeness_lock": [],
  "must_preserve": [],
  "must_avoid": []
}
```

## Prompt pattern

Keep generation prompts concrete and short:

```text
Original compact whole-body 3D-rendered chibi mascot, <archetype and personality>.
Identity: <silhouette>, <ratio>, <face>, <material>, <palette>, <attached accessory>.
Readable at pet size, coherent toy construction, no text, no logo, no scenery, no detached effects.
```

For a selfie, append: `Preserve only the reference person's visible hair, face silhouette, glasses/facial-hair cues, and chosen clothing colors; clearly stylized, no identity claims.`

Do not request a named living artist's style. Translate style words into material, lighting, shape, palette, and edge qualities.
