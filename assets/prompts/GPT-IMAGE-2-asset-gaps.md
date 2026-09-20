# GPT Image 2 — Asset Gaps & Redos

Prompt pack for everything the game is **missing** or that should be **re-done better**, based on an audit of `assets/`, `public/assets/generated/`, and the states the engine actually uses in `src/game/FightScene.ts`.

Everything here follows the existing **`assets/prompts/style-bible.md`** (detailed 8/16-bit pixel art, `#00ff00` chroma-key background, side-view, crisp outlines, no AA/blur/text). Run any of these through the existing pipeline:

```bash
npm run asset:generate -- assets/prompts/<file>.md public/assets/generated/<out>.png --size 1024x1024 --quality high
# then slice the chroma-key strip into per-frame PNGs with the existing scripts/slice-*.py
```

> Reuse the **character descriptions** verbatim from `fighter-kai.md` / `fighter-nova.md` in every character prompt so Kai and Nova stay on-model:
> - **Kai** — athletic compact street-martial-artist; teal sleeveless jacket, dark cropped pants, golden sash, fingerless gloves; short dark angular hair; warm skin.
> - **Nova** — precise confident kickboxer; crimson cropped combat jacket, dark violet leggings, light-blue wraps/trim; high ponytail; warm skin.

---

## Priority summary

**A. Missing character states the engine references but has no sprites for** (currently fall back to idle/heavy):
`block · landing · knockdown · wake (get-up) · ko (defeat) · victory · special-cast (Pulse) · super-cast (Overdrive) · throw (grab)`

**B. Re-do (quality):** character **portraits** (current ones are 64×64 and muddy) and the **projectile** art (single static image — make real travel + impact frames).

**C. Missing front-end screens & type:** **title screen**, **VS screen**, **character-select background**, and **word-art** (KO / FIGHT / ROUND / PERFECT / WINS) — all currently drawn as plain monospace text.

**D. Optional content:** 2 extra **stages**.

Generate each state for **both Kai and Nova** (swap the character block). Frame counts below match how the engine slices strips, so new states drop straight into `SPRITE_FRAME_COUNTS` / loaders.

---

# A · MISSING CHARACTER STATES

All character prompts share this scaffold — keep scale and foot baseline identical to the existing `idle` strip so frames align:

```
Draw an original 8-bit arcade fighting game character animation strip on a pure #00ff00 chroma key background.
Follow assets/prompts/style-bible.md. Detailed 8/16-bit pixel art, crisp dark outline, no blur, no
anti-aliasing, no painterly texture, no text labels.
Side-view fighting game perspective, character facing right, full body in frame, same scale and same
foot baseline on every frame, identical costume/face/hair/palette across all frames.
Character: <PASTE KAI OR NOVA DESCRIPTION>
```

### block  (3 frames) — needs wiring: add `block` to loaders, count 3
```
<SCAFFOLD>
Animation: high guard BLOCK. 3 frames in one horizontal row:
1 raising both forearms across the face and chest, weight settling back,
2 braced full guard, elbows tucked, slight lean away from incoming attack,
3 guard absorbing impact, body pushed back a touch, forearms tight.
Defensive, grounded, no attacking limbs extended.
```

### landing  (3 frames) — for the `landing` state after a jump
```
<SCAFFOLD>
Animation: LANDING from a jump. 3 frames in one horizontal row:
1 feet touching down, knees beginning to bend to absorb impact,
2 deep absorbing crouch, arms out slightly for balance,
3 rising back toward neutral stance. Small implied dust at the feet (still on chroma key).
```

### knockdown  (5 frames) — for `knockdown` (heavy/sweep/throw send-off)
```
<SCAFFOLD>
Animation: KNOCKDOWN, getting launched and falling backward. 5 frames in one horizontal row:
1 struck and recoiling, feet leaving the ground,
2 airborne, body tilting back, limbs trailing,
3 nearly horizontal, back toward the ground,
4 impact on the floor, dust implied,
5 lying on back on the ground, dazed. Readable, dramatic, no blood.
```

### wake  (4 frames) — for the `wake` get-up state
```
<SCAFFOLD>
Animation: WAKE-UP / getting back to feet. 4 frames in one horizontal row:
1 lying on the ground starting to push up,
2 up on one knee, hand on the floor,
3 rising, regaining balance,
4 back to neutral fighting stance. Determined expression.
```

### ko  (4 frames) — for the `ko` defeat state
```
<SCAFFOLD>
Animation: KO / DEFEAT collapse. 4 frames in one horizontal row:
1 final hit recoil, head snapping back,
2 legs buckling, falling,
3 crumpling toward the floor,
4 motionless on the ground, defeated. Dramatic, stylized, no gore.
```

### victory  (5 frames) — used at roundOver / matchOver (new state)
```
<SCAFFOLD>
Animation: VICTORY pose loop. 5 frames in one horizontal row, a short triumphant celebration:
1 lowering guard, relaxing,
2 turning toward camera,
3-4 signature confident victory pose (Kai: fist raised with golden-sash flourish; Nova: arms-crossed
confident smirk with ponytail flick),
5 holding the pose. Energetic, charismatic, in-character.
```

### special-cast "Pulse"  (5 frames) — the `special` projectile cast (currently borrows `heavy`)
```
<SCAFFOLD>
Animation: casting an energy PULSE projectile forward. 5 frames in one horizontal row:
1 winding up, drawing the rear hand back as cyan energy gathers in the palm,
2 energy charging brighter at the hip,
3 thrusting both palms forward releasing the pulse,
4 follow-through, arms extended, energy leaving the hands,
5 recovering toward stance. The released cyan energy orb should sit just past the hands.
Energy color cyan (#67e8f9).
```

### super-cast "Overdrive"  (6 frames) — the `super` (currently borrows `kick`)
```
<SCAFFOLD>
Animation: OVERDRIVE super move. 6 frames in one horizontal row:
1 dramatic charge stance, body wreathed in gathering magenta-pink energy,
2 energy peaking, hair/clothes lifted by the aura,
3 explosive forward lunge,
4 unleashing a large magenta-pink energy burst forward,
5 full extension, peak power,
6 recovery. Aura color magenta-pink (#f0abfc), high drama, bold readable silhouette.
```

### throw (grab)  (4 frames) — dedicated `throw` instead of reusing `heavy`
```
<SCAFFOLD>
Animation: close-range THROW. 4 frames in one horizontal row:
1 stepping in, arms reaching to grab,
2 seizing the (implied) opponent by the collar,
3 spinning/heaving them,
4 follow-through release. Show only THIS character; leave space where the thrown opponent would be.
```

---

# B · RE-DO (QUALITY)

### Portraits — re-do at high detail (current are 64×64 and muddy)
Generate one per fighter, then downscale in-engine instead of generating tiny.
```
Draw a detailed 8/16-bit arcade fighting game CHARACTER PORTRAIT bust on a pure #00ff00 chroma key background.
Follow assets/prompts/style-bible.md. Crisp dark outline, rich hand-placed pixel shading, no blur, no
anti-aliasing, no text. Head and shoulders, 3/4 angle, intense determined expression, dramatic rim
lighting, strong readable face pixels.
Character: <PASTE KAI OR NOVA DESCRIPTION>
```
Run with `--size 1024x1024`; save to `public/assets/generated/<kai|nova>/portrait.png` (engine already loads this path).

### Projectiles — re-do as real frames (current `projectile-special/super` are single static images)
**Pulse travel strip (4 frames):**
```
Draw a 4-frame energy projectile travel strip on a pure #00ff00 chroma key background. Follow
assets/prompts/style-bible.md, detailed 8/16-bit pixel art, crisp outline, no blur, no text.
A spinning cyan (#67e8f9) chi orb with a short comet tail, moving left-to-right: frame 1 forming small,
frames 2-3 full size travelling, frame 4 same size with a longer tail. No character.
```
**Overdrive travel strip (4 frames):** same as above but a larger **magenta-pink (#f0abfc)** energy sphere with crackling edges.

**Projectile impact burst (3 frames):**
```
Draw a 3-frame projectile IMPACT burst on a pure #00ff00 chroma key background. Follow style-bible.md.
Frame 1 compact flash, frame 2 expanding ring of energy shards, frame 3 dissipating sparks. Make a
cyan version and a magenta-pink version. Pixel art, crisp, no character, no text.
```

---

# C · FRONT-END SCREENS & WORD-ART

These are full scenes (NOT chroma key) — use the dusk neon-dojo palette from `stage-neon-dojo.md` so they match.

### Title screen (16:9)
```
Draw a detailed 8/16-bit arcade fighting game TITLE SCREEN, 16:9 landscape. Pixel art matching
assets/prompts/style-bible.md (neon-dusk palette: navy shadows, teal highlights, warm gold, crimson
accents, sunset sky). Two silhouetted fighters clashing dramatically behind a bold metallic beveled
arcade logo lockup, glowing embers, rooftop-neon-city backdrop. Leave clear lower-center space for a
"PRESS START" prompt. No real readable body text other than a placeholder logo shape.
```
Generate with `--size 1536x1024`.

### VS screen (16:9)
```
Draw an 8/16-bit fighting game VERSUS SCREEN, 16:9. Diagonal split, teal-gold left half vs crimson-violet
right half (Kai vs Nova colors), a large jagged "VS" emblem clashing at center, dramatic radial speed
lines, neon-dusk palette. Leave a framed empty portrait slot on each half (art dropped in by code).
Pixel art, crisp outlines, no other text.
```

### Character-select background (16:9)
```
Draw an 8/16-bit fighting game CHARACTER SELECT background, 16:9. A row of angular chrome portrait
frames (leave them EMPTY for code to fill), a "SELECT YOUR FIGHTER" banner area at top, neon-dusk arcade
backdrop with diagonal energy streaks matching the neon-dojo palette. Pixel art, crisp, readable.
```

### Word-art sheet (replaces plain monospace HUD text)
```
Draw 8/16-bit arcade fighting game WORD-ART on a pure #00ff00 chroma key background. Follow style-bible.md.
Bold chrome-and-crimson beveled arcade lettering with impact bursts behind each word. Generate these words,
ONE WORD PER IMAGE (run separately): "K.O." , "FIGHT!" , "ROUND" , "PERFECT" , "WINS" , "TIME OVER".
Crisp pixel edges, dramatic, no extra text.
```

---

# D · OPTIONAL EXTRA STAGES (16:9, match stage-neon-dojo.md format)

```
Draw a magnificent detailed 8-bit side-view fighting game arena background, 16:9. Follow style-bible.md
and the composition rules in stage-neon-dojo.md (clear horizontal fighting floor in the bottom quarter,
architecture mid-distance, dramatic sky behind; no characters/UI/text).
Scene: a rain-slicked NEON NIGHT MARKET alley — stacked signage in teal and crimson, paper lanterns,
steam vents, wet reflective tiled floor, distant skyline. Cool blue shadows, warm sign glow.
```
```
Draw a magnificent detailed 8-bit side-view fighting game arena background, 16:9. Follow style-bible.md
and stage-neon-dojo.md composition. Scene: a windswept MOUNTAIN TEMPLE COURTYARD at golden hour — stone
platform fighting floor, torii-like gate, prayer flags, distant snow peaks, warm gold light, long
shadows, drifting cherry petals.
```

---

## Wiring notes (so new sprites actually show up)
- New states (`block`, `landing`, `knockdown`, `wake`, `ko`, `victory`, `special`, `super`, `throw`) need entries in the preload loops + a `SPRITE_FRAME_COUNTS`-style table and the `renderFighter` switch in `FightScene.ts`. Today several of these states exist in logic but reuse `idle`/`heavy`/`kick` textures.
- Keep every character strip on the **same foot baseline and scale** as `idle` or the slicer/auto-scale will misalign them.
- After generating, run the matching `scripts/slice-*.py` (or add a slice step) and bump `ASSET_VERSION` in `FightScene.ts` to bust the `?v=` cache.
```
