# Fighting Game — Session Handoff

**Last updated:** 2026-07-04 (evening session)
**Project folder:** `D:\Google Workspace\Claude\Projects\fighting-game`

---

## TL;DR

**The 9 missing character states are DONE — generated, sliced, wired and tested.** The
OpenAI-key blocker is gone: art is now generated **locally** through ComfyUI
(Qwen-Image 2512 + Lightning, RTX 5090) — no API key, no cost.

All 9 states × both fighters now render real art (no idle/heavy fallbacks):
`block · landing · knockdown · wake · ko · victory · special (Pulse) · super (Overdrive) · throw`

Notes: `super` is **5 frames** (not the roadmap's 6 — the image model reliably draws 5);
`victory` is a fully wired new `FighterState` (winner plays it at round/match end).

## New local asset pipeline (replaces the OpenAI scripts)

- `scripts/comfy-generate.py` — text→image or **reference→image** via local ComfyUI API
  (`--ref` keeps the fighter on-model using `tmp/<fighter>-ref.png` reference sheets).
- `scripts/slice-state-strips.py` — chroma-key → island detection (merges detached
  effect orbs, splits aura-bridged poses, sanity-checks widths) → scale-normalized
  320×560 frames + manifest update. Density-crop keeps characters full-size when
  effect trails overflow the canvas.
- `scripts/batch-generate-states.py` — the whole loop with auto re-roll on bad frame
  counts. `--only kai-super,nova-block` to target specific states.
- Requires: local ComfyUI running on `127.0.0.1:8188` (it usually is), `py` (3.11)
  with pillow/numpy/scipy (installed).

## Engine changes this session (`src/game/FightScene.ts`)

- `EXTRA_STATE_FRAME_COUNTS` + `ATTACK_SPRITE_FRAME_COUNTS` tables; preload loops.
- `throw`/`special`/`super` have their own `spriteState` (were borrowing heavy/kick).
- New `victory` FighterState — set on the round winner in `endRound`; roundOver/matchOver
  now tick `stateTime` so win/KO animations play out.
- `blockFlash` on Fighter — blocked hits flash the block-impact frame (block-2).
- ko/knockdown/wake no longer fake poses by rotating hit/crouch sprites (graceful
  fallback with rotation kept if a texture is ever missing).
- `ASSET_VERSION = 'state-pack-002'`.
- Tests extended: `tests/jump-check.spec.ts` covers the new states + frame inventory.

## Phase 2 (same day, done)

- **Portraits** redone at high detail (224×224, chroma-keyed, `<fighter>/portrait.png`).
- **Projectiles** are real animations now: 4 travel frames + 3-frame impact bursts per
  attack (`vfx/projectile-<attack>-N.png`, `vfx/<attack>-impact-N.png`), wired with
  forming-frame → travel-loop logic and impact effects on hit.
- **Word-art** (K.O./FIGHT!/ROUND/PERFECT/WINS/TIME OVER) generated and wired:
  ROUND+digit at intro, FIGHT! flash, K.O./PERFECT/TIME OVER at round end
  (`showWordArt` in FightScene, falls back to text if textures missing).
- New script: `scripts/slice-vfx-strip.py` (chroma VFX/word-art slicer, `--single`,
  `--max-side`). `ASSET_VERSION = 'state-pack-003'`.

## Phase 3 (same day, done): real audio

- **13 SFX** generated with Stable Audio Open (`scripts/comfy-audio.py`, batch via
  `scripts/batch-generate-audio.py`) → trimmed/normalized WAVs in `public/assets/audio/`.
  `playSound` prefers them; the old WebAudio synth beeps remain as fallback.
- **3 music tracks** via ACE-Step 1.5 turbo: `music-fight` (64s loop), `music-menu`
  (48s loop), `music-victory` (12s sting). `playMusic()` switches on select/intro/matchOver;
  handles the browser audio-unlock gesture.
- Note: ComfyUI's `EmptyLatentAudio` rejects durations < 1.0s — generate ≥1s and let the
  post-process trim.

## What's left (from the original roadmap in `assets/prompts/GPT-IMAGE-2-asset-gaps.md`)

- **C. Front-end screens:** title screen, VS screen, char-select background.
- **D. Optional:** 2 extra stages ("WINS" word-art is generated but not yet wired).
- Minor polish: nova-ko frame 1 and nova-knockdown frames 0-1 are a bit static —
  re-roll with `py scripts/batch-generate-states.py --only nova-ko,nova-knockdown`
  if desired.

All of these can now use the same local pipeline (use the C-section prompts from the
roadmap with `scripts/comfy-generate.py`, no `--ref` needed for scenes/word-art).

## Verification

`npm run build` ✓ · `npm run test:animation` (Playwright; browsers must be installed
once per machine: `npx playwright install chromium chromium-headless-shell`).
