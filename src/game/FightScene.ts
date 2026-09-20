import Phaser from 'phaser'
import {
  consumeTouchJust,
  registerControl,
  type Control,
  type ControlName,
  type TouchPlayer,
} from './touch'

type PlayerId = 'p1' | 'p2'
type AssetKey =
  | 'kai'
  | 'nova'
  | 'dragon'
  | 'talon'
  | 'ryu'
  | 'kara'
  | 'blaze'
  | 'cyberon'
  | 'shadow'
  | 'luna'
  | 'titan'
const ROSTER: AssetKey[] = ['kai', 'nova', 'dragon', 'talon', 'ryu', 'kara', 'blaze', 'cyberon', 'shadow', 'luna', 'titan']
type GameMode = 'select' | 'intro' | 'fight' | 'roundOver' | 'matchOver'
type FighterState =
  | 'idle'
  | 'walk'
  | 'crouch'
  | 'jump'
  | 'landing'
  | 'block'
  | 'attack'
  | 'hit'
  | 'knockdown'
  | 'wake'
  | 'ko'
  | 'victory'
type AttackName =
  | 'light'
  | 'heavy'
  | 'kick'
  | 'crouchPunch'
  | 'crouchKick'
  | 'throw'
  | 'special'
  | 'super'
type AttackSpriteState = 'light' | 'heavy' | 'kick' | 'crouch-punch' | 'crouch-kick' | 'throw' | 'special' | 'super'
type HitReaction = 'stand' | 'crouch' | 'air'

type ControlKeys = Record<ControlName, Control>

type AttackDef = {
  name: AttackName
  label: string
  spriteState: AttackSpriteState
  damage: number
  chip: number
  startup: number
  active: number
  recovery: number
  range: number
  push: number
  stun: number
  yOffset: number
  height: number
  color: number
  hitStop: number
  meterGain: number
  cost?: number
  low?: boolean
  throw?: boolean
  projectile?: boolean
  knockdown?: boolean
}

type Fighter = {
  id: PlayerId
  name: string
  assetKey: AssetKey
  x: number
  y: number
  vx: number
  vy: number
  facing: -1 | 1
  health: number
  displayHealth: number
  maxHealth: number
  meter: number
  wins: number
  state: FighterState
  stateTime: number
  blockFlash: number
  currentAttack: AttackName | null
  attackConnected: boolean
  hitReaction: HitReaction
  grounded: boolean
  controls: ControlKeys
  sprite: Phaser.GameObjects.Image
  spriteScale: number
  shadow: Phaser.GameObjects.Graphics
  combo: number
  comboTimer: number
  dashTime: number
  dashDir: -1 | 1
  specialCooldown: number
  lastLeftTap: number
  lastRightTap: number
}

type FighterConfig = {
  name: string
  assetKey: AssetKey
  spriteScale: number
  tint: number
  trim: number
  accent: number
  stats: [number, number, number]
}

type Projectile = {
  owner: PlayerId
  attack: 'special' | 'super'
  x: number
  y: number
  vx: number
  life: number
  age: number
  color: number
  size: number
  sprite: Phaser.GameObjects.Image
}

type EffectKind = 'hit' | 'block' | 'super-hit' | 'dust' | 'special-impact' | 'super-impact'

type VisualEffect = {
  kind: EffectKind
  sprite: Phaser.GameObjects.Image
  vx: number
  vy: number
  life: number
  maxLife: number
  frameCount: number
  scaleStart: number
  scaleEnd: number
  rotationSpeed: number
}

const GAME_WIDTH = 960
const GAME_HEIGHT = 540
const GROUND_Y = 438
const GRAVITY = 1750
const WALK_SPEED = 250
const AIR_SPEED = 220
const AIR_CONTROL = 7.5
const DASH_SPEED = 520
const CROUCH_SPEED = 105
const JUMP_VELOCITY = -880
const ROUND_SECONDS = 99
const ASSET_VERSION = 'roster-001'
const SPRITE_STATES = ['idle', 'walk', 'crouch', 'jump', 'light', 'heavy', 'kick', 'hit'] as const
const SPRITE_FRAME_COUNTS = {
  idle: 8,
  walk: 8,
  crouch: 4,
  jump: 7,
  light: 5,
  heavy: 5,
  kick: 5,
  hit: 3,
} as const
const MOVEMENT_FRAME_COUNTS = {
  run: 5,
  jumpTuck: 6,
} as const
const CROUCH_ATTACK_STATES = ['crouch-punch', 'crouch-kick'] as const
const CROUCH_ATTACK_FRAME_COUNT = 5
const HIT_REACTION_STATES = ['crouch-hit', 'air-hit'] as const
const HIT_REACTION_FRAME_COUNT = 4
const EXTRA_STATE_FRAME_COUNTS = {
  block: 3,
  landing: 3,
  knockdown: 5,
  wake: 4,
  ko: 4,
  victory: 5,
  special: 5,
  super: 5,
  throw: 4,
} as const
const ATTACK_SPRITE_FRAME_COUNTS: Record<AttackSpriteState, number> = {
  light: 5,
  heavy: 5,
  kick: 5,
  'crouch-punch': 5,
  'crouch-kick': 5,
  throw: 4,
  special: 5,
  super: 5,
}
const VFX_FRAME_COUNTS: Record<EffectKind, number> = {
  hit: 8,
  block: 7,
  'super-hit': 9,
  dust: 7,
  'special-impact': 3,
  'super-impact': 3,
}
const PROJECTILE_TRAVEL_FRAMES = 4
const WORD_ART_KEYS = ['ko', 'fight', 'round', 'perfect', 'wins', 'timeover'] as const
type SoundKind =
  | 'menu'
  | 'round'
  | 'start'
  | 'jump'
  | 'dash'
  | 'hit'
  | 'block'
  | 'throw'
  | 'ko'
  | 'special'
  | 'super'
  | 'superHit'
  | 'deny'
const SFX_VOLUMES: Record<SoundKind, number> = {
  menu: 0.5,
  round: 0.8,
  start: 0.7,
  jump: 0.4,
  dash: 0.35,
  hit: 0.75,
  block: 0.6,
  throw: 0.8,
  ko: 0.9,
  special: 0.65,
  super: 0.85,
  superHit: 0.9,
  deny: 0.5,
}
const MUSIC_TRACKS = ['fight', 'menu', 'victory'] as const
type MusicTrack = (typeof MUSIC_TRACKS)[number]
// [special tint, super tint] — fighters without an entry keep the default cyan/magenta art.
const PROJECTILE_TINTS: Partial<Record<AssetKey, [number, number]>> = {
  dragon: [0x86efac, 0x5ef07a],
  talon: [0xf5f0e0, 0xf7e9c0],
  ryu: [0x93c5fd, 0x60a5fa],
  kara: [0xc084fc, 0xa855f7],
  blaze: [0xfb923c, 0xf97316],
  cyberon: [0x60a5fa, 0x3b82f6],
  shadow: [0x8b5cf6, 0x7c3aed],
  luna: [0xbae6fd, 0x7dd3fc],
  titan: [0xfbbf24, 0xd97706],
}
const DEFAULT_MOVEMENT_SCALE = { run: 1, jumpTuck: 1 }
const MOVEMENT_SCALE_MULTIPLIERS: Partial<Record<AssetKey, { run: number; jumpTuck: number }>> = {
  kai: {
    run: 1.24,
    jumpTuck: 1.22,
  },
  nova: {
    run: 1.45,
    jumpTuck: 1.42,
  },
}

const FIGHTERS: Record<AssetKey, FighterConfig> = {
  kai: {
    name: 'KAI',
    assetKey: 'kai',
    spriteScale: 0.52,
    tint: 0x2dd4bf,
    trim: 0xffd166,
    accent: 0x19d37c,
    stats: [88, 74, 82],
  },
  nova: {
    name: 'NOVA',
    assetKey: 'nova',
    spriteScale: 0.42,
    tint: 0xef476f,
    trim: 0x7dd3fc,
    accent: 0xff3e7f,
    stats: [72, 92, 86],
  },
  dragon: {
    name: 'DRAGON',
    assetKey: 'dragon',
    spriteScale: 0.5,
    tint: 0x3ea63e,
    trim: 0xf2c230,
    accent: 0x1b5e1b,
    stats: [96, 62, 90],
  },
  talon: {
    name: 'TALON',
    assetKey: 'talon',
    spriteScale: 0.5,
    tint: 0xb08428,
    trim: 0xf2d270,
    accent: 0x7a5f1e,
    stats: [84, 88, 78],
  },
  ryu: {
    name: 'RYU',
    assetKey: 'ryu',
    spriteScale: 0.5,
    tint: 0xef4444,
    trim: 0xfef3c7,
    accent: 0xb91c1c,
    stats: [80, 75, 90],
  },
  kara: {
    name: 'KARA',
    assetKey: 'kara',
    spriteScale: 0.46,
    tint: 0xa855f7,
    trim: 0xe9d5ff,
    accent: 0x7e22ce,
    stats: [70, 95, 85],
  },
  blaze: {
    name: 'BLAZE',
    assetKey: 'blaze',
    spriteScale: 0.5,
    tint: 0xf97316,
    trim: 0xfed7aa,
    accent: 0xc2410c,
    stats: [85, 65, 60],
  },
  cyberon: {
    name: 'CYBERON',
    assetKey: 'cyberon',
    spriteScale: 0.5,
    tint: 0x3b82f6,
    trim: 0xbfdbfe,
    accent: 0x1d4ed8,
    stats: [85, 75, 80],
  },
  shadow: {
    name: 'SHADOW',
    assetKey: 'shadow',
    spriteScale: 0.46,
    tint: 0x7c3aed,
    trim: 0xddd6fe,
    accent: 0x5b21b6,
    stats: [70, 95, 90],
  },
  luna: {
    name: 'LUNA',
    assetKey: 'luna',
    spriteScale: 0.46,
    tint: 0x38bdf8,
    trim: 0xe0f2fe,
    accent: 0x0369a1,
    stats: [70, 90, 85],
  },
  titan: {
    name: 'TITAN',
    assetKey: 'titan',
    spriteScale: 0.54,
    tint: 0xb45309,
    trim: 0xfde68a,
    accent: 0x78350f,
    stats: [120, 50, 60],
  },
}

const ATTACKS: Record<AttackName, AttackDef> = {
  light: {
    name: 'light',
    label: 'Jab',
    spriteState: 'light',
    damage: 6,
    chip: 1,
    startup: 70,
    active: 90,
    recovery: 145,
    range: 66,
    push: 115,
    stun: 210,
    yOffset: -92,
    height: 36,
    color: 0xf9d65c,
    hitStop: 78,
    meterGain: 9,
  },
  heavy: {
    name: 'heavy',
    label: 'Cross',
    spriteState: 'heavy',
    damage: 12,
    chip: 2,
    startup: 130,
    active: 95,
    recovery: 245,
    range: 82,
    push: 190,
    stun: 315,
    yOffset: -90,
    height: 44,
    color: 0xff7a3d,
    hitStop: 105,
    meterGain: 15,
    knockdown: true,
  },
  kick: {
    name: 'kick',
    label: 'Kick',
    spriteState: 'kick',
    damage: 10,
    chip: 2,
    startup: 110,
    active: 115,
    recovery: 225,
    range: 92,
    push: 170,
    stun: 280,
    yOffset: -62,
    height: 38,
    color: 0x8be9fd,
    hitStop: 95,
    meterGain: 13,
    knockdown: true,
  },
  crouchPunch: {
    name: 'crouchPunch',
    label: 'Low punch',
    spriteState: 'crouch-punch',
    damage: 5,
    chip: 1,
    startup: 70,
    active: 95,
    recovery: 145,
    range: 78,
    push: 95,
    stun: 210,
    yOffset: -64,
    height: 32,
    color: 0xfde68a,
    hitStop: 72,
    meterGain: 8,
    low: true,
  },
  crouchKick: {
    name: 'crouchKick',
    label: 'Sweep',
    spriteState: 'crouch-kick',
    damage: 8,
    chip: 1,
    startup: 95,
    active: 115,
    recovery: 220,
    range: 108,
    push: 150,
    stun: 285,
    yOffset: -34,
    height: 30,
    color: 0x7dd3fc,
    hitStop: 98,
    meterGain: 12,
    low: true,
    knockdown: true,
  },
  throw: {
    name: 'throw',
    label: 'Throw',
    spriteState: 'throw',
    damage: 14,
    chip: 0,
    startup: 70,
    active: 90,
    recovery: 260,
    range: 48,
    push: 310,
    stun: 420,
    yOffset: -98,
    height: 124,
    color: 0xfacc15,
    hitStop: 125,
    meterGain: 18,
    throw: true,
    knockdown: true,
  },
  special: {
    name: 'special',
    label: 'Pulse',
    spriteState: 'special',
    damage: 9,
    chip: 2,
    startup: 105,
    active: 40,
    recovery: 280,
    range: 0,
    push: 155,
    stun: 260,
    yOffset: -86,
    height: 36,
    color: 0x67e8f9,
    hitStop: 92,
    meterGain: 6,
    cost: 25,
    projectile: true,
  },
  super: {
    name: 'super',
    label: 'Overdrive',
    spriteState: 'super',
    damage: 24,
    chip: 5,
    startup: 150,
    active: 55,
    recovery: 420,
    range: 0,
    push: 270,
    stun: 520,
    yOffset: -88,
    height: 52,
    color: 0xf0abfc,
    hitStop: 160,
    meterGain: 0,
    cost: 100,
    projectile: true,
    knockdown: true,
  },
}

function keyboard(scene: Phaser.Scene): Phaser.Input.Keyboard.KeyboardPlugin {
  if (!scene.input.keyboard) {
    throw new Error('Keyboard input is required for the fighting prototype.')
  }

  return scene.input.keyboard
}

function makeControls(
  scene: Phaser.Scene,
  player: TouchPlayer,
  codes: Record<ControlName, number>,
): ControlKeys {
  const input = keyboard(scene)
  const names: ControlName[] = ['left', 'right', 'up', 'down', 'block', 'light', 'heavy', 'kick']
  const controls = {} as ControlKeys

  for (const name of names) {
    const control: Control = {
      key: input.addKey(codes[name]),
      touchDown: false,
      touchJust: false,
    }
    registerControl(player, name, control)
    controls[name] = control
  }

  return controls
}

function isKeyDown(control: Control): boolean {
  return control.key.isDown || control.touchDown
}

function justDown(control: Control): boolean {
  // Both sides are read unconditionally: `||` would short-circuit and leave
  // a touch edge flag set, firing again on the next call this frame.
  const fromKey = Phaser.Input.Keyboard.JustDown(control.key)
  const fromTouch = consumeTouchJust(control)
  return fromKey || fromTouch
}

function clamp01(value: number): number {
  return Phaser.Math.Clamp(value, 0, 1)
}

export class FightScene extends Phaser.Scene {
  private playerOne!: Fighter
  private playerTwo!: Fighter
  private hud!: Phaser.GameObjects.Graphics
  private stageFx!: Phaser.GameObjects.Graphics
  private combatFx!: Phaser.GameObjects.Graphics
  private overlay!: Phaser.GameObjects.Graphics
  private message!: Phaser.GameObjects.Text
  private hudPortraitP1!: Phaser.GameObjects.Image
  private hudPortraitP2!: Phaser.GameObjects.Image
  private wordArt!: Phaser.GameObjects.Image
  private wordArtDigit!: Phaser.GameObjects.Image
  private music: Phaser.Sound.BaseSound | null = null
  private musicKey = ''
  private selectInfo!: Phaser.GameObjects.Text
  private selectLabelP1!: Phaser.GameObjects.Text
  private selectLabelP2!: Phaser.GameObjects.Text
  private selectP1!: Phaser.GameObjects.Image
  private selectP2!: Phaser.GameObjects.Image
  private mode: GameMode = 'select'
  private modeTime = 0
  private roundTime = ROUND_SECONDS
  private roundNumber = 1
  private selected: Record<PlayerId, AssetKey> = { p1: 'kai', p2: 'nova' }
  private projectiles: Projectile[] = []
  private effects: VisualEffect[] = []
  private hitStopMs = 0
  private stageImpact = 0
  private matchWinner: PlayerId | 'draw' | null = null
  private audioContext: AudioContext | null = null
  private restarting = false
  private hudHealthFrameP1!: Phaser.GameObjects.Image
  private hudHealthFrameP2!: Phaser.GameObjects.Image
  private hudHealthTrackP1!: Phaser.GameObjects.Image
  private hudHealthTrackP2!: Phaser.GameObjects.Image
  private hudHealthLagP1!: Phaser.GameObjects.Image
  private hudHealthLagP2!: Phaser.GameObjects.Image
  private hudHealthFillP1!: Phaser.GameObjects.Image
  private hudHealthFillP2!: Phaser.GameObjects.Image
  private hudMeterFrameP1!: Phaser.GameObjects.Image
  private hudMeterFrameP2!: Phaser.GameObjects.Image
  private hudTimerFrame!: Phaser.GameObjects.Image
  private hudTimerTens!: Phaser.GameObjects.Image
  private hudTimerOnes!: Phaser.GameObjects.Image
  private hudPipsP1: Phaser.GameObjects.Image[] = []
  private hudPipsP2: Phaser.GameObjects.Image[] = []

  constructor() {
    super('FightScene')
  }

  preload(): void {
    this.load.image('stage-neon-dojo', `/assets/generated/stage-neon-dojo-001.png?v=${ASSET_VERSION}`)
    this.load.image('ui-health-frame', `/assets/generated/ui/health-frame.png?v=${ASSET_VERSION}`)
    this.load.image('ui-health-track', `/assets/generated/ui/health-track.png?v=${ASSET_VERSION}`)
    this.load.image('ui-health-lag', `/assets/generated/ui/health-lag.png?v=${ASSET_VERSION}`)
    this.load.image('ui-health-fill-p1', `/assets/generated/ui/health-fill-p1.png?v=${ASSET_VERSION}`)
    this.load.image('ui-health-fill-p2', `/assets/generated/ui/health-fill-p2.png?v=${ASSET_VERSION}`)
    this.load.image('ui-meter-frame', `/assets/generated/ui/meter-frame.png?v=${ASSET_VERSION}`)
    this.load.image('ui-timer-frame', `/assets/generated/ui/timer-frame.png?v=${ASSET_VERSION}`)
    this.load.image('ui-round-pip-empty', `/assets/generated/ui/round-pip-empty.png?v=${ASSET_VERSION}`)
    this.load.image('ui-round-pip-full', `/assets/generated/ui/round-pip-full.png?v=${ASSET_VERSION}`)

    for (let index = 0; index <= 9; index += 1) {
      this.load.image(`ui-digit-${index}`, `/assets/generated/ui/digit-${index}.png?v=${ASSET_VERSION}`)
    }

    for (const [kind, count] of Object.entries(VFX_FRAME_COUNTS)) {
      for (let index = 0; index < count; index += 1) {
        this.load.image(`vfx-${kind}-${index}`, `/assets/generated/vfx/${kind}-${index}.png?v=${ASSET_VERSION}`)
      }
    }
    this.load.image('vfx-projectile-special', `/assets/generated/vfx/projectile-special.png?v=${ASSET_VERSION}`)
    this.load.image('vfx-projectile-super', `/assets/generated/vfx/projectile-super.png?v=${ASSET_VERSION}`)

    for (const attack of ['special', 'super'] as const) {
      for (let index = 0; index < PROJECTILE_TRAVEL_FRAMES; index += 1) {
        this.load.image(
          `vfx-projectile-${attack}-${index}`,
          `/assets/generated/vfx/projectile-${attack}-${index}.png?v=${ASSET_VERSION}`,
        )
      }
    }

    for (const word of WORD_ART_KEYS) {
      this.load.image(`ui-word-${word}`, `/assets/generated/vfx/wordart-${word}.png?v=${ASSET_VERSION}`)
    }

    for (const kind of Object.keys(SFX_VOLUMES)) {
      this.load.audio(`sfx-${kind}`, `/assets/audio/${kind}.wav?v=${ASSET_VERSION}`)
    }
    for (const track of MUSIC_TRACKS) {
      this.load.audio(`music-${track}`, `/assets/audio/music-${track}.mp3?v=${ASSET_VERSION}`)
    }

    for (const fighter of ROSTER) {
      for (const state of SPRITE_STATES) {
        this.load.image(`${fighter}-${state}`, `/assets/generated/${fighter}/${state}.png?v=${ASSET_VERSION}`)
      }

      for (const [state, count] of Object.entries(SPRITE_FRAME_COUNTS)) {
        for (let index = 0; index < count; index += 1) {
          const key = state === 'jump' ? `${fighter}-jump-bent-${index}` : `${fighter}-${state}-${index}`
          this.load.image(key, `/assets/generated/${fighter}/${state}-${index}.png?v=${ASSET_VERSION}`)
        }
      }

      for (let index = 0; index < MOVEMENT_FRAME_COUNTS.run; index += 1) {
        this.load.image(`${fighter}-run-${index}`, `/assets/generated/${fighter}/run-${index}.png?v=${ASSET_VERSION}`)
      }

      for (let index = 0; index < MOVEMENT_FRAME_COUNTS.jumpTuck; index += 1) {
        this.load.image(
          `${fighter}-jump-tuck-${index}`,
          `/assets/generated/${fighter}/jump-tuck-${index}.png?v=${ASSET_VERSION}`,
        )
      }

      for (const state of CROUCH_ATTACK_STATES) {
        for (let index = 0; index < CROUCH_ATTACK_FRAME_COUNT; index += 1) {
          this.load.image(
            `${fighter}-${state}-${index}`,
            `/assets/generated/${fighter}/${state}-${index}.png?v=${ASSET_VERSION}`,
          )
        }
      }

      for (const state of HIT_REACTION_STATES) {
        for (let index = 0; index < HIT_REACTION_FRAME_COUNT; index += 1) {
          this.load.image(
            `${fighter}-${state}-${index}`,
            `/assets/generated/${fighter}/${state}-${index}.png?v=${ASSET_VERSION}`,
          )
        }
      }

      for (const [state, count] of Object.entries(EXTRA_STATE_FRAME_COUNTS)) {
        for (let index = 0; index < count; index += 1) {
          this.load.image(
            `${fighter}-${state}-${index}`,
            `/assets/generated/${fighter}/${state}-${index}.png?v=${ASSET_VERSION}`,
          )
        }
      }

      this.load.image(`${fighter}-portrait`, `/assets/generated/${fighter}/portrait.png?v=${ASSET_VERSION}`)
    }
  }

  create(): void {
    this.cameras.main.setBackgroundColor(0x10172a)
    this.drawStage()

    this.stageFx = this.add.graphics().setDepth(5)
    this.combatFx = this.add.graphics().setDepth(24)
    this.hud = this.add.graphics().setDepth(30)
    this.overlay = this.add.graphics().setDepth(40)
    this.hudPortraitP1 = this.add.image(50, 46, 'kai-portrait').setOrigin(0.5).setDepth(31).setVisible(false)
    this.hudPortraitP2 = this.add.image(GAME_WIDTH - 58, 46, 'nova-portrait').setOrigin(0.5).setDepth(31).setVisible(false)
    this.wordArt = this.add.image(GAME_WIDTH / 2, 196, '__DEFAULT').setOrigin(0.5).setDepth(43).setVisible(false)
    this.wordArtDigit = this.add.image(GAME_WIDTH / 2, 196, '__DEFAULT').setOrigin(0.5).setDepth(43).setVisible(false)
    this.hudHealthTrackP1 = this.add.image(92, 24, 'ui-health-track').setOrigin(0, 0).setDepth(31).setVisible(false)
    this.hudHealthTrackP2 = this.add.image(GAME_WIDTH - 378, 24, 'ui-health-track').setOrigin(0, 0).setDepth(31).setVisible(false)
    this.hudHealthLagP1 = this.add.image(92, 24, 'ui-health-lag').setOrigin(0, 0).setDepth(32).setVisible(false)
    this.hudHealthLagP2 = this.add.image(GAME_WIDTH - 378, 24, 'ui-health-lag').setOrigin(0, 0).setDepth(32).setVisible(false)
    this.hudHealthFillP1 = this.add.image(92, 24, 'ui-health-fill-p1').setOrigin(0, 0).setDepth(32).setVisible(false)
    this.hudHealthFillP2 = this.add.image(GAME_WIDTH - 378, 24, 'ui-health-fill-p2').setOrigin(0, 0).setDepth(32).setVisible(false)
    this.hudHealthFrameP1 = this.add.image(82, 17, 'ui-health-frame').setOrigin(0, 0).setDepth(33).setVisible(false)
    this.hudHealthFrameP2 = this.add.image(GAME_WIDTH - 388, 17, 'ui-health-frame').setOrigin(0, 0).setDepth(33).setVisible(false)
    this.hudMeterFrameP1 = this.add.image(87, 56, 'ui-meter-frame').setOrigin(0, 0).setDepth(31).setVisible(false)
    this.hudMeterFrameP2 = this.add.image(GAME_WIDTH - 383, 56, 'ui-meter-frame').setOrigin(0, 0).setDepth(31).setVisible(false)
    this.hudTimerFrame = this.add.image(GAME_WIDTH / 2, 46, 'ui-timer-frame').setOrigin(0.5).setDepth(31).setVisible(false)
    this.hudTimerTens = this.add.image(GAME_WIDTH / 2 - 15, 48, 'ui-digit-9').setOrigin(0.5).setDepth(32).setVisible(false)
    this.hudTimerOnes = this.add.image(GAME_WIDTH / 2 + 15, 48, 'ui-digit-9').setOrigin(0.5).setDepth(32).setVisible(false)
    this.hudPipsP1 = [0, 1].map((index) =>
      this.add.image(GAME_WIDTH / 2 - 86 + index * 18 + 8, 86, 'ui-round-pip-empty').setDepth(32).setVisible(false),
    )
    this.hudPipsP2 = [0, 1].map((index) =>
      this.add.image(GAME_WIDTH / 2 + 66 - index * 18, 86, 'ui-round-pip-empty').setDepth(32).setVisible(false),
    )

    this.message = this.add.text(GAME_WIDTH / 2, 76, '', {
      align: 'center',
      color: '#fff7ad',
      fontFamily: 'Consolas, monospace',
      fontSize: '24px',
      fontStyle: 'bold',
      stroke: '#0f172a',
      strokeThickness: 6,
    })
    this.message.setOrigin(0.5, 0)
    this.message.setDepth(42)

    this.selectInfo = this.add.text(GAME_WIDTH / 2, 132, '', {
      align: 'center',
      color: '#dbeafe',
      fontFamily: 'Consolas, monospace',
      fontSize: '14px',
      lineSpacing: 6,
      stroke: '#020617',
      strokeThickness: 4,
    })
    this.selectInfo.setOrigin(0.5, 0)
    this.selectInfo.setDepth(42)

    this.selectP1 = this.add.image(256, 386, 'kai-idle-0').setOrigin(0.5, 1).setScale(0.45).setDepth(42)
    this.selectP2 = this.add.image(704, 386, 'nova-idle-0').setOrigin(0.5, 1).setScale(0.36).setDepth(42)
    this.selectLabelP1 = this.createSelectLabel()
    this.selectLabelP2 = this.createSelectLabel()

    this.playerOne = this.createFighter('p1', this.selected.p1, 274, 1, this.p1Controls())
    this.playerTwo = this.createFighter('p2', this.selected.p2, 686, -1, this.p2Controls())
    this.hideFighters()

    this.addControlsText()
    this.bindInput()
    this.sound.once(Phaser.Sound.Events.UNLOCKED, () => {
      if (this.music && !this.music.isPlaying) {
        this.music.play()
      }
    })
    this.enterSelect()
  }

  update(time: number, delta: number): void {
    const dt = Math.min(delta, 34)
    this.modeTime += dt
    this.updateEffectTimers(dt)

    if (this.mode === 'select') {
      this.drawStageFx(time)
      this.drawCombatFx()
      this.drawSelectScreen(time)
      return
    }

    if (this.mode === 'intro') {
      if (this.modeTime > 1050 && this.modeTime <= 1500) {
        if (this.showWordArt('fight')) {
          this.message.setText('')
        } else {
          this.message.setText('FIGHT!')
        }
      }
      if (this.modeTime > 1500) {
        this.mode = 'fight'
        this.modeTime = 0
        this.message.setText('')
        this.playSound('start')
      }
    }

    // Let the FIGHT! word-art linger briefly into the round, then clear it.
    if (this.mode === 'fight' && this.wordArt.visible && this.modeTime > 450) {
      this.showWordArt(null)
    }

    if (this.mode === 'fight') {
      if (this.hitStopMs > 0) {
        this.hitStopMs = Math.max(0, this.hitStopMs - dt)
      } else {
        this.roundTime = Math.max(0, this.roundTime - dt / 1000)
        this.updateFighter(this.playerOne, this.playerTwo, dt)
        this.updateFighter(this.playerTwo, this.playerOne, dt)
        this.updateProjectiles(dt)
        this.resolveBodyPush()
        this.checkRoundEnd()
      }
    }

    if (this.mode === 'roundOver' || this.mode === 'matchOver') {
      for (const fighter of [this.playerOne, this.playerTwo]) {
        fighter.stateTime += dt
        if (!fighter.grounded) {
          this.applyGravity(fighter, dt / 1000)
          this.clampFighter(fighter)
        }
      }
    }

    this.playerOne.facing = this.playerOne.x <= this.playerTwo.x ? 1 : -1
    this.playerTwo.facing = this.playerTwo.x <= this.playerOne.x ? 1 : -1

    this.drawStageFx(time)
    this.drawCombatFx()
    this.renderFighter(this.playerOne, time)
    this.renderFighter(this.playerTwo, time)
    this.drawHud()
    this.drawFlowOverlay()
  }

  private p1Controls(): ControlKeys {
    return makeControls(this, 'p1', {
      left: Phaser.Input.Keyboard.KeyCodes.A,
      right: Phaser.Input.Keyboard.KeyCodes.D,
      up: Phaser.Input.Keyboard.KeyCodes.W,
      down: Phaser.Input.Keyboard.KeyCodes.S,
      block: Phaser.Input.Keyboard.KeyCodes.Q,
      light: Phaser.Input.Keyboard.KeyCodes.E,
      heavy: Phaser.Input.Keyboard.KeyCodes.R,
      kick: Phaser.Input.Keyboard.KeyCodes.T,
    })
  }

  private p2Controls(): ControlKeys {
    return makeControls(this, 'p2', {
      left: Phaser.Input.Keyboard.KeyCodes.LEFT,
      right: Phaser.Input.Keyboard.KeyCodes.RIGHT,
      up: Phaser.Input.Keyboard.KeyCodes.UP,
      down: Phaser.Input.Keyboard.KeyCodes.DOWN,
      block: Phaser.Input.Keyboard.KeyCodes.I,
      light: Phaser.Input.Keyboard.KeyCodes.O,
      heavy: Phaser.Input.Keyboard.KeyCodes.P,
      kick: Phaser.Input.Keyboard.KeyCodes.L,
    })
  }

  private bindInput(): void {
    const input = keyboard(this)
    input.on('keydown', (event: KeyboardEvent) => {
      this.unlockAudio()
      this.handleKey(event)
    })
    this.input.on('pointerdown', () => {
      this.unlockAudio()
      if (this.mode === 'select') {
        this.startMatch()
      } else if (this.mode === 'roundOver' || this.mode === 'matchOver') {
        this.advanceAfterRound()
      }
    })
  }

  private cycleFighter(current: AssetKey, direction: number): AssetKey {
    const next = (ROSTER.indexOf(current) + direction + ROSTER.length) % ROSTER.length
    return ROSTER[next]
  }

  private handleKey(event: KeyboardEvent): void {
    if (this.mode === 'select') {
      if (event.code === 'KeyA' || event.code === 'KeyD') {
        this.selected.p1 = this.cycleFighter(this.selected.p1, event.code === 'KeyA' ? -1 : 1)
        this.playSound('menu')
      }
      if (event.code === 'ArrowLeft' || event.code === 'ArrowRight') {
        this.selected.p2 = this.cycleFighter(this.selected.p2, event.code === 'ArrowLeft' ? -1 : 1)
        this.playSound('menu')
      }
      if (event.code === 'Enter' || event.code === 'Space') {
        this.startMatch()
      }
      return
    }

    if (this.mode === 'roundOver' || this.mode === 'matchOver') {
      if (event.code === 'Enter' || event.code === 'Space' || event.code === 'KeyR') {
        event.preventDefault()
        this.advanceAfterRound()
      }
    }
  }

  private addControlsText(): void {
    this.add.text(22, GAME_HEIGHT - 44, 'P1  A/D move  W jump  S low  Q block  E/R/T attack  Q+E pulse  Q+T super', {
      color: '#dbeafe',
      fontFamily: 'Consolas, monospace',
      fontSize: '12px',
    }).setDepth(31)

    const p2 = this.add.text(
      GAME_WIDTH - 22,
      GAME_HEIGHT - 44,
      'P2  arrows move  I block  O/P/L attack  I+O pulse  I+L super',
      {
        color: '#fee2e2',
        fontFamily: 'Consolas, monospace',
        fontSize: '12px',
      },
    )
    p2.setOrigin(1, 0)
    p2.setDepth(31)

    this.add.text(GAME_WIDTH / 2, GAME_HEIGHT - 20, 'Best of 3   Enter/click advances   Q+R / I+P close throw', {
      color: '#fde68a',
      fontFamily: 'Consolas, monospace',
      fontSize: '12px',
    }).setOrigin(0.5).setDepth(31)
  }

  private enterSelect(): void {
    this.mode = 'select'
    this.modeTime = 0
    this.matchWinner = null
    this.roundNumber = 1
    this.showWordArt(null)
    this.playMusic('menu')
    this.clearCombatAssets()
    this.hitStopMs = 0
    this.hideFighters()
    this.hud.clear()
    this.hideHudAssets()
  }

  private hideHudAssets(): void {
    for (const image of [
      this.hudPortraitP1,
      this.hudPortraitP2,
      this.hudHealthFrameP1,
      this.hudHealthFrameP2,
      this.hudHealthTrackP1,
      this.hudHealthTrackP2,
      this.hudHealthLagP1,
      this.hudHealthLagP2,
      this.hudHealthFillP1,
      this.hudHealthFillP2,
      this.hudMeterFrameP1,
      this.hudMeterFrameP2,
      this.hudTimerFrame,
      this.hudTimerTens,
      this.hudTimerOnes,
      ...this.hudPipsP1,
      ...this.hudPipsP2,
    ]) {
      image.setVisible(false)
    }
  }

  private clearCombatAssets(): void {
    for (const projectile of this.projectiles) {
      projectile.sprite.destroy()
    }
    for (const effect of this.effects) {
      effect.sprite.destroy()
    }
    this.projectiles = []
    this.effects = []
    this.combatFx.clear()
  }

  private startMatch(): void {
    this.roundNumber = 1
    this.matchWinner = null
    this.playerOne.wins = 0
    this.playerTwo.wins = 0
    this.startRound(true)
  }

  private startRound(resetMeter: boolean): void {
    const p1Wins = this.playerOne?.wins ?? 0
    const p2Wins = this.playerTwo?.wins ?? 0
    const p1Meter = resetMeter ? 0 : (this.playerOne?.meter ?? 0)
    const p2Meter = resetMeter ? 0 : (this.playerTwo?.meter ?? 0)

    this.destroyFighters()
    this.playerOne = this.createFighter('p1', this.selected.p1, 274, 1, this.p1Controls())
    this.playerTwo = this.createFighter('p2', this.selected.p2, 686, -1, this.p2Controls())
    this.playerOne.wins = p1Wins
    this.playerTwo.wins = p2Wins
    this.playerOne.meter = p1Meter
    this.playerTwo.meter = p2Meter
    this.roundTime = ROUND_SECONDS
    this.clearCombatAssets()
    this.hitStopMs = 0
    this.mode = 'intro'
    this.modeTime = 0
    this.playMusic('fight')
    if (this.showWordArt('round', { digit: Math.min(9, this.roundNumber) })) {
      this.message.setText('')
    } else {
      this.message.setText(`ROUND ${this.roundNumber}`)
    }
    this.selectInfo.setText('')
    this.selectP1.setVisible(false)
    this.selectP2.setVisible(false)
    this.selectLabelP1.setVisible(false)
    this.selectLabelP2.setVisible(false)
    this.playSound('round')
  }

  private advanceAfterRound(): void {
    if (this.restarting) {
      return
    }

    if (this.mode === 'matchOver') {
      this.enterSelect()
      return
    }

    this.roundNumber += 1
    this.startRound(false)
  }

  private createFighter(id: PlayerId, assetKey: AssetKey, x: number, facing: -1 | 1, controls: ControlKeys): Fighter {
    const config = FIGHTERS[assetKey]
    const sprite = this.add.image(x, GROUND_Y, `${assetKey}-idle-0`)
    sprite.setOrigin(0.5, 1)
    sprite.setScale(config.spriteScale)
    sprite.setDepth(id === 'p1' ? 12 : 13)

    return {
      id,
      name: config.name,
      assetKey,
      x,
      y: GROUND_Y,
      vx: 0,
      vy: 0,
      facing,
      health: 100,
      displayHealth: 100,
      maxHealth: 100,
      meter: 0,
      wins: 0,
      state: 'idle',
      stateTime: 0,
      blockFlash: 0,
      currentAttack: null,
      attackConnected: false,
      hitReaction: 'stand',
      grounded: true,
      controls,
      sprite,
      spriteScale: config.spriteScale,
      shadow: this.add.graphics(),
      combo: 0,
      comboTimer: 0,
      dashTime: 0,
      dashDir: facing,
      specialCooldown: 0,
      lastLeftTap: -1000,
      lastRightTap: -1000,
    }
  }

  private destroyFighters(): void {
    for (const fighter of [this.playerOne, this.playerTwo]) {
      if (!fighter) {
        continue
      }
      fighter.sprite.destroy()
      fighter.shadow.destroy()
    }
  }

  private hideFighters(): void {
    for (const fighter of [this.playerOne, this.playerTwo]) {
      fighter.sprite.setVisible(false)
      fighter.shadow.clear()
    }
  }

  private updateFighter(fighter: Fighter, opponent: Fighter, dt: number): void {
    const seconds = dt / 1000
    fighter.stateTime += dt
    fighter.comboTimer = Math.max(0, fighter.comboTimer - dt)
    fighter.blockFlash = Math.max(0, fighter.blockFlash - dt)
    fighter.specialCooldown = Math.max(0, fighter.specialCooldown - dt)
    fighter.displayHealth = Phaser.Math.Linear(fighter.displayHealth, fighter.health, Math.min(1, seconds * 5.2))

    if (fighter.comboTimer <= 0) {
      fighter.combo = 0
    }

    if (fighter.state === 'ko' || fighter.state === 'victory') {
      return
    }

    if (fighter.state === 'hit' && fighter.stateTime >= this.hitStunFor(fighter)) {
      this.setState(fighter, this.recoveryState(fighter))
    }

    if (fighter.state === 'knockdown') {
      this.applyGravity(fighter, seconds)
      fighter.vx = Phaser.Math.Linear(fighter.vx, 0, Math.min(1, seconds * 3.6))
      fighter.x += fighter.vx * seconds
      if (fighter.grounded && fighter.stateTime > 620) {
        this.setState(fighter, 'wake')
      }
      this.clampFighter(fighter)
      return
    }

    if (fighter.state === 'wake') {
      fighter.vx = 0
      if (fighter.stateTime > 250) {
        this.setState(fighter, 'idle')
      }
      return
    }

    if (fighter.state === 'landing') {
      fighter.vx = Phaser.Math.Linear(fighter.vx, 0, Math.min(1, 12 * seconds))
      if (fighter.stateTime >= 135) {
        this.setState(fighter, 'idle')
      }
      return
    }

    const canAct = fighter.state !== 'attack' && fighter.state !== 'hit'
    if (canAct) {
      this.readMovement(fighter, dt)
      this.readActions(fighter, opponent)
    } else {
      fighter.x += fighter.vx * seconds
      fighter.vx = Phaser.Math.Linear(fighter.vx, 0, Math.min(1, 9 * seconds))
    }

    if (!fighter.grounded) {
      this.applyGravity(fighter, seconds)
    }

    this.clampFighter(fighter)

    if (fighter.state === 'attack') {
      this.updateAttack(fighter, opponent)
    }
  }

  private readMovement(fighter: Fighter, dt: number): void {
    const controls = fighter.controls
    const seconds = dt / 1000
    const crouching = isKeyDown(controls.down) && fighter.grounded
    const blocking = isKeyDown(controls.block) && fighter.grounded
    const move = (isKeyDown(controls.right) ? 1 : 0) - (isKeyDown(controls.left) ? 1 : 0)

    if (!fighter.grounded) {
      fighter.dashTime = 0
      const targetVx = move * AIR_SPEED
      fighter.vx = Phaser.Math.Linear(fighter.vx, targetVx, Math.min(1, AIR_CONTROL * seconds))
      fighter.x += fighter.vx * seconds
      this.setState(fighter, 'jump')
      return
    }

    this.readDashTap(fighter)
    if (fighter.dashTime > 0) {
      fighter.dashTime = Math.max(0, fighter.dashTime - dt)
      fighter.vx = fighter.dashDir * DASH_SPEED
      fighter.x += fighter.vx * seconds
      this.setState(fighter, 'walk')
      return
    }

    if (justDown(controls.up) && fighter.grounded && !crouching && !blocking) {
      fighter.grounded = false
      fighter.vy = JUMP_VELOCITY
      fighter.vx = move * WALK_SPEED * 0.92
      this.setState(fighter, 'jump')
      this.spawnDust(fighter.x, GROUND_Y - 6, fighter.facing)
      this.playSound('jump')
      return
    }

    if (blocking) {
      fighter.vx = 0
      this.setState(fighter, crouching ? 'crouch' : 'block')
      return
    }

    if (crouching) {
      fighter.vx = move * CROUCH_SPEED
      fighter.x += fighter.vx * seconds
      this.setState(fighter, 'crouch')
      return
    }

    fighter.vx = move * WALK_SPEED
    fighter.x += fighter.vx * seconds
    this.setState(fighter, move === 0 ? 'idle' : 'walk')
  }

  private readDashTap(fighter: Fighter): void {
    const now = this.time.now
    if (justDown(fighter.controls.left)) {
      if (now - fighter.lastLeftTap < 260) {
        this.startDash(fighter, -1)
      }
      fighter.lastLeftTap = now
    }

    if (justDown(fighter.controls.right)) {
      if (now - fighter.lastRightTap < 260) {
        this.startDash(fighter, 1)
      }
      fighter.lastRightTap = now
    }
  }

  private startDash(fighter: Fighter, dir: -1 | 1): void {
    if (!fighter.grounded || isKeyDown(fighter.controls.down)) {
      return
    }
    fighter.dashDir = dir
    fighter.dashTime = 155
    this.playSound('dash')
  }

  private readActions(fighter: Fighter, opponent: Fighter): void {
    if (!fighter.grounded) {
      return
    }

    const blockHeld = isKeyDown(fighter.controls.block)
    const lowAttack = fighter.grounded && (fighter.state === 'crouch' || isKeyDown(fighter.controls.down))
    const close = Math.abs(fighter.x - opponent.x) < 92

    if (blockHeld && justDown(fighter.controls.kick) && fighter.meter >= (ATTACKS.super.cost ?? 100)) {
      this.startAttack(fighter, 'super')
      return
    }

    if (blockHeld && justDown(fighter.controls.light) && fighter.meter >= (ATTACKS.special.cost ?? 25)) {
      this.startAttack(fighter, 'special')
      return
    }

    if (blockHeld && justDown(fighter.controls.heavy) && close) {
      this.startAttack(fighter, 'throw')
      return
    }

    if (fighter.state === 'block') {
      return
    }

    if (lowAttack) {
      if (justDown(fighter.controls.light) || justDown(fighter.controls.heavy)) {
        this.startAttack(fighter, 'crouchPunch')
      } else if (justDown(fighter.controls.kick)) {
        this.startAttack(fighter, 'crouchKick')
      }
      return
    }

    if (justDown(fighter.controls.light)) {
      this.startAttack(fighter, 'light')
    } else if (justDown(fighter.controls.heavy)) {
      this.startAttack(fighter, 'heavy')
    } else if (justDown(fighter.controls.kick)) {
      this.startAttack(fighter, 'kick')
    }
  }

  private startAttack(fighter: Fighter, attackName: AttackName): void {
    const attack = ATTACKS[attackName]
    if (attack.cost && fighter.meter < attack.cost) {
      this.playSound('deny')
      return
    }

    if (attack.cost) {
      fighter.meter = Math.max(0, fighter.meter - attack.cost)
    }

    fighter.currentAttack = attackName
    fighter.attackConnected = false
    fighter.vx = 0
    this.setState(fighter, 'attack')
    if (attack.projectile) {
      this.playSound(attackName === 'super' ? 'super' : 'special')
    }
  }

  private updateAttack(attacker: Fighter, defender: Fighter): void {
    if (!attacker.currentAttack) {
      this.setState(attacker, 'idle')
      return
    }

    const attack = ATTACKS[attacker.currentAttack]
    const total = attack.startup + attack.active + attack.recovery
    const isActive = attacker.stateTime >= attack.startup && attacker.stateTime <= attack.startup + attack.active

    if (attack.projectile && isActive && !attacker.attackConnected) {
      this.spawnProjectile(attacker, attack.name === 'super' ? 'super' : 'special')
      attacker.attackConnected = true
    } else if (!attack.projectile && isActive && !attacker.attackConnected && this.attackOverlaps(attacker, defender, attack)) {
      this.applyHit(attacker, defender, attack)
      attacker.attackConnected = true
    }

    if (attacker.stateTime >= total) {
      attacker.currentAttack = null
      attacker.attackConnected = false
      this.setState(attacker, this.recoveryState(attacker))
    }
  }

  private attackOverlaps(attacker: Fighter, defender: Fighter, attack: AttackDef): boolean {
    const hitbox = this.getAttackRect(attacker, attack)
    const hurtbox = this.getHurtRect(defender)
    return Phaser.Geom.Intersects.RectangleToRectangle(hitbox, hurtbox)
  }

  private applyHit(attacker: Fighter, defender: Fighter, attack: AttackDef): void {
    const defenderBlocking = this.isBlocking(defender, attacker, attack)
    const wasAirborne = !defender.grounded
    const wasCrouched = !wasAirborne && this.isLowProfile(defender)
    const damage = defenderBlocking ? attack.chip : attack.damage
    const push = defenderBlocking ? attack.push * 0.62 : attack.push

    defender.health = Math.max(0, defender.health - damage)
    defender.vx = attacker.facing * (wasCrouched ? push * 0.72 : push)
    defender.currentAttack = null
    defender.attackConnected = false

    if (defenderBlocking) {
      defender.meter = Math.min(100, defender.meter + 8)
      defender.blockFlash = 220
      this.setState(defender, isKeyDown(defender.controls.down) ? 'crouch' : 'block')
      this.spawnImpact(defender.x - attacker.facing * 28, defender.y - 92, attack.color, true)
      this.hitStopMs = Math.max(this.hitStopMs, Math.floor(attack.hitStop * 0.55))
      this.cameras.main.shake(45, 0.002)
      this.playSound('block')
      return
    }

    attacker.meter = Math.min(100, attacker.meter + attack.meterGain)
    attacker.combo = attacker.comboTimer > 0 ? attacker.combo + 1 : 1
    attacker.comboTimer = 1450

    if (defender.health <= 0) {
      defender.health = 0
      defender.vx = attacker.facing * 120
      defender.vy = -95
      defender.grounded = false
      this.setState(defender, 'ko')
    } else if (attack.knockdown || attack.throw) {
      defender.vy = attack.throw ? -260 : -145
      defender.grounded = false
      this.setState(defender, 'knockdown')
    } else {
      defender.hitReaction = wasAirborne ? 'air' : wasCrouched ? 'crouch' : 'stand'
      if (defender.hitReaction === 'air') {
        defender.vy = Math.min(defender.vy, -180)
        defender.grounded = false
      } else {
        defender.vy = 0
        defender.y = GROUND_Y
        defender.grounded = true
      }
      this.setState(defender, 'hit', true)
    }

    this.hitStopMs = Math.max(this.hitStopMs, attack.hitStop)
    this.spawnImpact(defender.x - attacker.facing * 18, defender.y + attack.yOffset, attack.color, false)
    this.flashDefender(defender)
    this.cameras.main.shake(attack.name === 'super' ? 135 : 75, attack.name === 'super' ? 0.008 : 0.004)
    this.playSound(attack.throw ? 'throw' : attack.name === 'super' ? 'superHit' : 'hit')
  }

  private spawnProjectile(attacker: Fighter, attack: 'special' | 'super'): void {
    const def = ATTACKS[attack]
    const animated = this.textures.exists(`vfx-projectile-${attack}-0`)
    const sprite = this.add
      .image(
        attacker.x + attacker.facing * 78,
        attacker.y + def.yOffset,
        animated ? `vfx-projectile-${attack}-0` : `vfx-projectile-${attack}`,
      )
      .setOrigin(0.5)
      .setDepth(23)
      .setFlipX(attacker.facing === -1)
      .setScale(animated ? (attack === 'super' ? 0.42 : 0.32) : attack === 'super' ? 0.82 : 0.68)
    const tints = PROJECTILE_TINTS[attacker.assetKey]
    if (tints) {
      sprite.setTint(attack === 'super' ? tints[1] : tints[0])
    }
    this.projectiles.push({
      owner: attacker.id,
      attack,
      x: sprite.x,
      y: sprite.y,
      vx: attacker.facing * (attack === 'super' ? 620 : 470),
      life: attack === 'super' ? 1250 : 1050,
      age: 0,
      color: def.color,
      size: attack === 'super' ? 18 : 10,
      sprite,
    })
  }

  private updateProjectiles(dt: number): void {
    const seconds = dt / 1000
    const remaining: Projectile[] = []
    for (const projectile of this.projectiles) {
      projectile.life -= dt
      projectile.age += dt
      projectile.x += projectile.vx * seconds
      projectile.sprite.setPosition(projectile.x, projectile.y)

      const travelKey = `vfx-projectile-${projectile.attack}-0`
      if (this.textures.exists(travelKey)) {
        // Real travel frames: brief forming frame, then loop the travel cycle.
        const frame =
          projectile.age < 90 ? 0 : 1 + (Math.floor((projectile.age - 90) / 85) % (PROJECTILE_TRAVEL_FRAMES - 1))
        const frameKey = `vfx-projectile-${projectile.attack}-${frame}`
        if (projectile.sprite.texture.key !== frameKey) {
          projectile.sprite.setTexture(frameKey)
        }
        projectile.sprite.setScale((projectile.attack === 'super' ? 0.42 : 0.32) + Math.sin(this.time.now / 48) * 0.02)
      } else {
        projectile.sprite.angle += (projectile.attack === 'super' ? 260 : 180) * seconds
        projectile.sprite.setScale((projectile.attack === 'super' ? 0.82 : 0.68) + Math.sin(this.time.now / 48) * 0.04)
      }

      const defender = projectile.owner === 'p1' ? this.playerTwo : this.playerOne
      const attacker = projectile.owner === 'p1' ? this.playerOne : this.playerTwo
      const rect = new Phaser.Geom.Rectangle(
        projectile.x - projectile.size,
        projectile.y - projectile.size,
        projectile.size * 2,
        projectile.size * 2,
      )
      if (Phaser.Geom.Intersects.RectangleToRectangle(rect, this.getHurtRect(defender))) {
        this.applyHit(attacker, defender, ATTACKS[projectile.attack])
        if (this.textures.exists(`vfx-${projectile.attack}-impact-0`)) {
          this.spawnEffect(`${projectile.attack}-impact`, projectile.x + Math.sign(projectile.vx) * 14, projectile.y, {
            life: projectile.attack === 'super' ? 340 : 260,
            rotationSpeed: 0,
            scaleStart: projectile.attack === 'super' ? 0.55 : 0.45,
            scaleEnd: projectile.attack === 'super' ? 0.95 : 0.75,
          })
        }
        projectile.life = 0
      }

      if (projectile.life > 0 && projectile.x > -80 && projectile.x < GAME_WIDTH + 80) {
        remaining.push(projectile)
      } else {
        projectile.sprite.destroy()
      }
    }
    this.projectiles = remaining
  }

  private isBlocking(defender: Fighter, attacker: Fighter, attack: AttackDef): boolean {
    if (attack.throw || !defender.grounded || defender.facing !== -attacker.facing) {
      return false
    }

    const blockHeld = isKeyDown(defender.controls.block)
    if (!blockHeld) {
      return false
    }

    return attack.low ? isKeyDown(defender.controls.down) || defender.state === 'crouch' : true
  }

  private applyGravity(fighter: Fighter, seconds: number): void {
    fighter.vy += GRAVITY * seconds
    fighter.y += fighter.vy * seconds
    fighter.x += fighter.vx * seconds

    if (fighter.y >= GROUND_Y) {
      fighter.y = GROUND_Y
      fighter.vy = 0
      fighter.grounded = true
      if (fighter.state === 'jump') {
        this.setState(fighter, 'landing')
        this.spawnDust(fighter.x, GROUND_Y - 6, fighter.facing)
      }
    }
  }

  private clampFighter(fighter: Fighter): void {
    fighter.x = Phaser.Math.Clamp(fighter.x, 64, GAME_WIDTH - 64)
  }

  private resolveBodyPush(): void {
    const distance = this.playerTwo.x - this.playerOne.x
    const minDistance = 62
    if (Math.abs(distance) >= minDistance) {
      return
    }

    const correction = (minDistance - Math.abs(distance)) / 2
    if (distance >= 0) {
      this.playerOne.x -= correction
      this.playerTwo.x += correction
    } else {
      this.playerOne.x += correction
      this.playerTwo.x -= correction
    }
    this.clampFighter(this.playerOne)
    this.clampFighter(this.playerTwo)
  }

  private checkRoundEnd(): void {
    if (this.mode !== 'fight') {
      return
    }

    if (this.playerOne.health > 0 && this.playerTwo.health > 0 && this.roundTime > 0) {
      return
    }

    const p1Win = this.playerOne.health > this.playerTwo.health
    const p2Win = this.playerTwo.health > this.playerOne.health
    if (p1Win) {
      this.playerOne.wins += 1
    } else if (p2Win) {
      this.playerTwo.wins += 1
    }

    const winnerText = p1Win ? `${this.playerOne.name} WINS` : p2Win ? `${this.playerTwo.name} WINS` : 'DRAW'
    const perfect = (p1Win && this.playerOne.health === this.playerOne.maxHealth) || (p2Win && this.playerTwo.health === this.playerTwo.maxHealth)
    const detail = this.roundTime <= 0 ? 'TIME OVER' : perfect ? 'PERFECT' : 'KO'
    const detailShown = this.showWordArt(
      this.roundTime <= 0 ? 'timeover' : perfect ? 'perfect' : 'ko',
      { y: 210 },
    )

    if (this.playerOne.health <= 0) {
      this.setState(this.playerOne, 'ko')
    }
    if (this.playerTwo.health <= 0) {
      this.setState(this.playerTwo, 'ko')
    }
    if (p1Win && this.playerOne.health > 0) {
      this.setState(this.playerOne, 'victory')
    }
    if (p2Win && this.playerTwo.health > 0) {
      this.setState(this.playerTwo, 'victory')
    }

    if (this.playerOne.wins >= 2 || this.playerTwo.wins >= 2) {
      this.mode = 'matchOver'
      this.matchWinner = this.playerOne.wins > this.playerTwo.wins ? 'p1' : this.playerTwo.wins > this.playerOne.wins ? 'p2' : 'draw'
      this.playMusic('victory')
      this.message.setText(detailShown ? `${winnerText}\nMATCH COMPLETE` : `${winnerText}\n${detail}\nMATCH COMPLETE`)
    } else {
      this.mode = 'roundOver'
      this.message.setText(
        detailShown
          ? `${winnerText}\nENTER / CLICK FOR ROUND ${this.roundNumber + 1}`
          : `${winnerText}\n${detail}\nENTER / CLICK FOR ROUND ${this.roundNumber + 1}`,
      )
    }
    this.modeTime = 0
    this.playSound('ko')
  }

  private hitStunFor(fighter: Fighter): number {
    if (fighter.hitReaction === 'air') {
      return 390
    }

    if (fighter.hitReaction === 'crouch') {
      return 255
    }

    return 290
  }

  private recoveryState(fighter: Fighter): FighterState {
    if (!fighter.grounded) {
      return 'jump'
    }

    return isKeyDown(fighter.controls.down) ? 'crouch' : 'idle'
  }

  private setState(fighter: Fighter, state: FighterState, restart = false): void {
    if (fighter.state === state && !restart) {
      return
    }
    fighter.state = state
    fighter.stateTime = 0
    if (state !== 'hit') {
      fighter.hitReaction = 'stand'
    }
  }

  private getAttackRect(fighter: Fighter, attack: AttackDef): Phaser.Geom.Rectangle {
    const x = fighter.x + fighter.facing * (34 + attack.range / 2)
    const y = fighter.y + attack.yOffset
    return new Phaser.Geom.Rectangle(x - attack.range / 2, y - attack.height / 2, attack.range, attack.height)
  }

  private getHurtRect(fighter: Fighter): Phaser.Geom.Rectangle {
    const crouch = this.isLowProfile(fighter)
    const knocked = fighter.state === 'knockdown' || fighter.state === 'ko'
    const height = knocked ? 62 : crouch ? 118 : 188
    const width = knocked ? 120 : crouch ? 72 : 66
    return new Phaser.Geom.Rectangle(fighter.x - width / 2, fighter.y - height, width, height)
  }

  private isLowProfile(fighter: Fighter): boolean {
    return (
      fighter.state === 'crouch' ||
      (fighter.state === 'hit' && fighter.hitReaction === 'crouch') ||
      (fighter.state === 'attack' &&
        (fighter.currentAttack === 'crouchPunch' || fighter.currentAttack === 'crouchKick'))
    )
  }

  private updateEffectTimers(dt: number): void {
    this.stageImpact = Math.max(0, this.stageImpact - dt / 220)
    const remaining: VisualEffect[] = []
    for (const effect of this.effects) {
      effect.life -= dt
      effect.sprite.x += effect.vx * (dt / 1000)
      effect.sprite.y += effect.vy * (dt / 1000)
      effect.vy += effect.kind === 'dust' ? -12 * (dt / 1000) : 320 * (dt / 1000)

      const progress = clamp01(1 - effect.life / effect.maxLife)
      const frame = Math.min(effect.frameCount - 1, Math.floor(progress * effect.frameCount))
      effect.sprite.setTexture(`vfx-${effect.kind}-${frame}`)
      effect.sprite.setScale(Phaser.Math.Linear(effect.scaleStart, effect.scaleEnd, progress))
      effect.sprite.setAlpha(effect.kind === 'dust' ? clamp01(1 - progress) : clamp01(1 - progress * 0.86))
      effect.sprite.angle += effect.rotationSpeed * (dt / 1000)

      if (effect.life > 0) {
        remaining.push(effect)
      } else {
        effect.sprite.destroy()
      }
    }
    this.effects = remaining
  }

  private spawnImpact(x: number, y: number, color: number, blocked: boolean): void {
    this.stageImpact = blocked ? 0.45 : 1
    const kind: EffectKind = blocked ? 'block' : color === ATTACKS.super.color ? 'super-hit' : 'hit'
    this.spawnEffect(kind, x, y, {
      life: blocked ? 280 : kind === 'super-hit' ? 520 : 390,
      scaleEnd: blocked ? 0.95 : kind === 'super-hit' ? 1.35 : 1.12,
      scaleStart: blocked ? 0.62 : 0.82,
    })

    const count = blocked ? 3 : kind === 'super-hit' ? 5 : 4
    for (let i = 0; i < count; i += 1) {
      const angle = (Math.PI * 2 * i) / count + Phaser.Math.FloatBetween(-0.25, 0.25)
      const speed = Phaser.Math.Between(blocked ? 60 : 115, blocked ? 145 : 255)
      this.spawnEffect(kind, x + Phaser.Math.Between(-8, 8), y + Phaser.Math.Between(-8, 8), {
        life: Phaser.Math.Between(170, blocked ? 260 : 340),
        rotationSpeed: Phaser.Math.FloatBetween(-90, 90),
        scaleEnd: blocked ? 0.32 : 0.42,
        scaleStart: blocked ? 0.18 : 0.24,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed - Phaser.Math.Between(30, 130),
      })
    }
  }

  private spawnDust(x: number, y: number, facing: -1 | 1): void {
    this.spawnEffect('dust', x, y, {
      life: 430,
      rotationSpeed: 0,
      scaleEnd: 1.2,
      scaleStart: 0.82,
      vx: -facing * 28,
      vy: -22,
    })
  }

  private spawnEffect(
    kind: EffectKind,
    x: number,
    y: number,
    options: Partial<Pick<VisualEffect, 'life' | 'rotationSpeed' | 'scaleEnd' | 'scaleStart' | 'vx' | 'vy'>>,
  ): void {
    const frameCount = VFX_FRAME_COUNTS[kind]
    const life = options.life ?? 360
    const sprite = this.add.image(x, y, `vfx-${kind}-0`).setOrigin(0.5).setDepth(25)
    const scaleStart = options.scaleStart ?? 1
    sprite.setScale(scaleStart)
    this.effects.push({
      kind,
      sprite,
      vx: options.vx ?? 0,
      vy: options.vy ?? 0,
      life,
      maxLife: life,
      frameCount,
      scaleStart,
      scaleEnd: options.scaleEnd ?? 1,
      rotationSpeed: options.rotationSpeed ?? Phaser.Math.FloatBetween(-45, 45),
    })
  }

  private flashDefender(defender: Fighter): void {
    if (!defender.sprite.visible) {
      return
    }
    defender.sprite.setTintFill(0xffffff)
    this.time.delayedCall(90, () => {
      defender.sprite.clearTint()
    })
  }

  private drawHud(): void {
    this.hud.clear()
    this.hud.setDepth(30)
    this.drawPortrait(22, 18, this.playerOne, false, this.hudPortraitP1)
    this.drawPortrait(GAME_WIDTH - 86, 18, this.playerTwo, true, this.hudPortraitP2)
    this.drawHealthBar(
      92,
      24,
      286,
      this.playerOne,
      false,
      this.hudHealthFrameP1,
      this.hudHealthTrackP1,
      this.hudHealthLagP1,
      this.hudHealthFillP1,
    )
    this.drawHealthBar(
      GAME_WIDTH - 378,
      24,
      286,
      this.playerTwo,
      true,
      this.hudHealthFrameP2,
      this.hudHealthTrackP2,
      this.hudHealthLagP2,
      this.hudHealthFillP2,
    )
    this.drawMeter(92, 60, 286, this.playerOne, false, this.hudMeterFrameP1)
    this.drawMeter(GAME_WIDTH - 378, 60, 286, this.playerTwo, true, this.hudMeterFrameP2)
    this.drawRoundPips(this.playerOne.wins, this.hudPipsP1)
    this.drawRoundPips(this.playerTwo.wins, this.hudPipsP2)
    this.drawTimer(Math.ceil(this.roundTime))
    this.drawCombo(this.playerOne, 132, 94, false)
    this.drawCombo(this.playerTwo, GAME_WIDTH - 132, 94, true)
  }

  private showWordArt(word: (typeof WORD_ART_KEYS)[number] | null, options?: { digit?: number; y?: number }): boolean {
    if (word === null || !this.textures.exists(`ui-word-${word}`)) {
      this.wordArt.setVisible(false)
      this.wordArtDigit.setVisible(false)
      return false
    }

    const y = options?.y ?? 196
    const texture = this.textures.get(`ui-word-${word}`).getSourceImage()
    const scale = Math.min(1, 300 / texture.width)
    const digit = options?.digit !== undefined && this.textures.exists(`ui-digit-${options.digit}`)
    const shift = digit ? -34 : 0
    this.wordArt
      .setTexture(`ui-word-${word}`)
      .setPosition(GAME_WIDTH / 2 + shift, y)
      .setScale(scale)
      .setVisible(true)
    if (digit) {
      this.wordArtDigit
        .setTexture(`ui-digit-${options!.digit}`)
        .setPosition(GAME_WIDTH / 2 + (texture.width * scale) / 2 + shift + 30, y)
        .setScale(2.2)
        .setVisible(true)
    } else {
      this.wordArtDigit.setVisible(false)
    }
    return true
  }

  private drawPortrait(
    x: number,
    y: number,
    fighter: Fighter,
    flip: boolean,
    portrait: Phaser.GameObjects.Image,
  ): void {
    const config = FIGHTERS[fighter.assetKey]
    this.hud.fillStyle(0x030712, 0.98)
    this.hud.fillRoundedRect(x - 3, y - 3, 62, 62, 7)
    this.hud.fillStyle(config.tint, 0.22)
    this.hud.fillRect(x + 3, y + 3, 50, 50)
    portrait
      .setTexture(`${fighter.assetKey}-portrait`)
      .setPosition(x + 28, y + 28)
      .setDisplaySize(56, 56)
      .setFlipX(flip)
      .setVisible(true)
    this.hud.lineStyle(2, config.trim, 0.92)
    this.hud.strokeRoundedRect(x - 1, y - 1, 58, 58, 6)
    this.hud.lineStyle(1, 0xfef3c7, 0.7)
    this.hud.strokeRoundedRect(x + 4, y + 4, 48, 48, 4)
  }

  private drawHealthBar(
    x: number,
    y: number,
    width: number,
    fighter: Fighter,
    flip: boolean,
    frame: Phaser.GameObjects.Image,
    track: Phaser.GameObjects.Image,
    lag: Phaser.GameObjects.Image,
    fill: Phaser.GameObjects.Image,
  ): void {
    const pct = clamp01(fighter.health / fighter.maxHealth)
    const lagPct = clamp01(fighter.displayHealth / fighter.maxHealth)
    const fillWidth = Math.floor(width * pct)
    const lagWidth = Math.floor(width * lagPct)
    const height = 24

    track
      .setPosition(x, y)
      .setOrigin(0, 0)
      .setFlipX(false)
      .setCrop(0, 0, width, height)
      .setVisible(true)
    this.drawHealthLayer(lag, 'ui-health-lag', x, y, width, height, lagWidth, flip)
    this.drawHealthLayer(
      fill,
      fighter.id === 'p1' ? 'ui-health-fill-p1' : 'ui-health-fill-p2',
      x,
      y,
      width,
      height,
      fillWidth,
      flip,
    )
    frame.setPosition(x - 10, y - 7).setFlipX(flip).setVisible(true)
  }

  private drawHealthLayer(
    image: Phaser.GameObjects.Image,
    texture: string,
    x: number,
    y: number,
    width: number,
    height: number,
    visibleWidth: number,
    alignRight: boolean,
  ): void {
    const drawWidth = Phaser.Math.Clamp(visibleWidth, 0, width)
    if (drawWidth <= 0) {
      image.setVisible(false)
      return
    }

    image
      .setTexture(texture)
      .setPosition(alignRight ? x + width - drawWidth : x, y)
      .setOrigin(0, 0)
      .setFlipX(false)
      .setCrop(0, 0, drawWidth, height)
      .setVisible(true)
  }

  private drawMeter(
    x: number,
    y: number,
    width: number,
    fighter: Fighter,
    flip: boolean,
    frame: Phaser.GameObjects.Image,
  ): void {
    const fill = Math.floor(width * clamp01(fighter.meter / 100))
    const fillX = flip ? x + width - fill : x
    frame.setPosition(x - 5, y - 4).setFlipX(flip).setVisible(true)
    this.hud.fillStyle(0x020617, 0.9)
    this.hud.fillRect(x, y, width, 8)
    this.hud.fillStyle(fighter.meter >= 100 ? 0xf0abfc : FIGHTERS[fighter.assetKey].trim, 1)
    this.hud.fillRect(fillX, y + 1, fill, 6)
  }

  private drawRoundPips(wins: number, pips: Phaser.GameObjects.Image[]): void {
    pips.forEach((pip, index) => {
      pip.setTexture(index < wins ? 'ui-round-pip-full' : 'ui-round-pip-empty').setVisible(true)
    })
  }

  private drawTimer(value: number): void {
    const digits = Phaser.Math.Clamp(value, 0, 99).toString().padStart(2, '0')
    this.hudTimerFrame.setVisible(true)
    this.hudTimerTens.setTexture(`ui-digit-${digits[0]}`).setVisible(true)
    this.hudTimerOnes.setTexture(`ui-digit-${digits[1]}`).setVisible(true)
  }

  private drawCombo(fighter: Fighter, x: number, y: number, flip: boolean): void {
    if (fighter.combo < 2 || fighter.comboTimer <= 0) {
      return
    }
    const text = `${fighter.combo} HIT`
    const w = text.length * 16 + 18
    const left = flip ? x - w : x
    this.hud.fillStyle(0x030712, 0.78)
    this.hud.fillRoundedRect(left, y, w, 28, 5)
    this.hud.fillStyle(FIGHTERS[fighter.assetKey].trim, 1)
    this.hud.fillRect(left + 8, y + 7, w - 16, 4)
    this.drawHudText(text, flip ? x - w + 12 : x + 12, y + 10, 0xfff7ad)
  }

  private drawHudText(text: string, x: number, y: number, color: number): void {
    this.hud.fillStyle(0x020617, 0.75)
    this.hud.fillRect(x + 2, y + 2, text.length * 8, 10)
    this.hud.fillStyle(color, 1)
    for (let i = 0; i < text.length; i += 1) {
      if (text[i] !== ' ') {
        this.hud.fillRect(x + i * 8, y, 5, 8)
      }
    }
  }

  private drawStage(): void {
    const stage = this.add.image(GAME_WIDTH / 2, GAME_HEIGHT / 2, 'stage-neon-dojo')
    stage.setDisplaySize(GAME_WIDTH, GAME_HEIGHT)
    stage.setDepth(0)

    const floorPolish = this.add.graphics()
    floorPolish.setDepth(1)
    floorPolish.fillStyle(0x050509, 0.16)
    floorPolish.fillRect(0, GROUND_Y - 18, GAME_WIDTH, GAME_HEIGHT - GROUND_Y + 18)
    floorPolish.lineStyle(2, 0xfacc15, 0.32)
    floorPolish.lineBetween(0, GROUND_Y - 18, GAME_WIDTH, GROUND_Y - 18)
  }

  private drawStageFx(time: number): void {
    this.stageFx.clear()
    this.stageFx.setDepth(5)
    const pulse = (offset: number, speed = 360): number => 0.5 + Math.sin(time / speed + offset) * 0.5

    this.drawPixelCloud(time, 78, 0.012, 0x91c7ff, 0.16, 1.1, 120)
    this.drawPixelCloud(time, 116, 0.018, 0xf8b58f, 0.13, 0.82, 540)
    this.drawPixelCloud(time, 154, 0.026, 0x7dd3fc, 0.1, 0.62, 850)

    for (const [x, y] of [[126, 158], [220, 160], [316, 163], [832, 240]] as const) {
      const alpha = 0.1 + pulse(x * 0.03, 520) * 0.12 + this.stageImpact * 0.08
      this.stageFx.fillStyle(0xff7a18, alpha)
      this.stageFx.fillCircle(x + Math.sin(time / 740 + x) * 2, y, 30)
      this.stageFx.fillStyle(0xfacc15, alpha * 0.65)
      this.stageFx.fillCircle(x, y, 17)
    }

    for (const ventX of [115, 830]) {
      for (let i = 0; i < 7; i += 1) {
        const drift = (time / 36 + i * 19) % 86
        const x = ventX + Math.sin(time / 420 + i) * 10 + i * 2
        const y = GROUND_Y - 72 - drift
        const alpha = Phaser.Math.Clamp(0.25 - drift / 420, 0, 0.22)
        this.stageFx.fillStyle(0xdbeafe, alpha)
        this.stageFx.fillEllipse(x, y, 30 + i * 3, 12 + i)
      }
    }

    for (let i = 0; i < 28; i += 1) {
      const x = (i * 79 + time / 42) % (GAME_WIDTH + 40) - 20
      const y = 114 + ((i * 37 + Math.floor(time / 65)) % 240)
      const alpha = 0.08 + pulse(i, 280) * 0.08 + this.stageImpact * 0.08
      this.stageFx.fillStyle(i % 2 === 0 ? 0x5eead4 : 0xfacc15, alpha)
      this.stageFx.fillRect(x, y, 3, 10 + (i % 3) * 3)
    }

    for (let i = 0; i < 16; i += 1) {
      const x = (i * 67 + time / 16) % (GAME_WIDTH + 80) - 40
      const y = 250 + ((i * 53 + time / 28) % 230)
      this.stageFx.lineStyle(1, 0xbfefff, 0.12)
      this.stageFx.lineBetween(x, y, x - 11, y + 26)
    }

    for (let i = 0; i < 8; i += 1) {
      const y = GROUND_Y + 8 + i * 9
      const shimmer = Math.sin(time / 260 + i) * (18 + this.stageImpact * 16)
      this.stageFx.lineStyle(1, i % 2 === 0 ? 0x38bdf8 : 0xf59e0b, 0.08 + this.stageImpact * 0.05)
      this.stageFx.lineBetween(190 + shimmer, y, 770 + shimmer, y + 18)
    }
  }

  private drawPixelCloud(
    time: number,
    baseY: number,
    speed: number,
    color: number,
    alpha: number,
    scale: number,
    offset: number,
  ): void {
    const cloudWidth = 280 * scale
    const span = GAME_WIDTH + cloudWidth
    const baseX = (((offset - time * speed) % span) + span) % span - cloudWidth
    const y = baseY + Math.sin(time / 1800 + offset) * 7
    const blocks = [
      [0, 20, 68, 18],
      [42, 8, 78, 28],
      [112, 0, 74, 36],
      [172, 13, 96, 25],
      [78, 34, 145, 14],
      [212, 38, 52, 12],
    ] as const

    for (const x of [baseX, baseX + span]) {
      this.stageFx.fillStyle(color, alpha)
      for (const [bx, by, bw, bh] of blocks) {
        this.stageFx.fillRect(x + bx * scale, y + by * scale, bw * scale, bh * scale)
      }
      this.stageFx.fillStyle(0xffffff, alpha * 0.42)
      this.stageFx.fillRect(x + 112 * scale, y + 8 * scale, 38 * scale, 7 * scale)
      this.stageFx.fillRect(x + 190 * scale, y + 22 * scale, 48 * scale, 6 * scale)
    }
  }

  private drawCombatFx(): void {
    this.combatFx.clear()
  }

  private drawSelectScreen(time: number): void {
    this.overlay.clear()
    this.overlay.fillStyle(0x020617, 0.72)
    this.overlay.fillRect(0, 0, GAME_WIDTH, GAME_HEIGHT)

    this.message.setText('ARCADE ROSTER')
    this.selectInfo.setText(
      'P1: A/D chooses      P2: arrows choose\nENTER / CLICK TO FIGHT',
    )
    this.drawSelectCard(88, 184, 336, this.selected.p1, 'PLAYER 1', false, this.selectLabelP1)
    this.drawSelectCard(536, 184, 336, this.selected.p2, 'PLAYER 2', true, this.selectLabelP2)

    this.selectP1.setVisible(true)
    this.selectP1.setTexture(`${this.selected.p1}-idle-${Math.floor(time / 120) % SPRITE_FRAME_COUNTS.idle}`)
    this.selectP1.setScale(FIGHTERS[this.selected.p1].spriteScale * 0.95)
    this.selectP1.setPosition(260, 434 + Math.sin(time / 220) * 3)
    this.selectP1.setFlipX(false)

    this.selectP2.setVisible(true)
    this.selectP2.setTexture(`${this.selected.p2}-idle-${Math.floor(time / 120) % SPRITE_FRAME_COUNTS.idle}`)
    this.selectP2.setScale(FIGHTERS[this.selected.p2].spriteScale * 0.95)
    this.selectP2.setPosition(700, 434 + Math.sin(time / 240 + 1) * 3)
    this.selectP2.setFlipX(true)
  }

  private drawSelectCard(
    x: number,
    y: number,
    width: number,
    assetKey: AssetKey,
    label: string,
    flip: boolean,
    labelText: Phaser.GameObjects.Text,
  ): void {
    const fighter = FIGHTERS[assetKey]
    this.overlay.fillStyle(0x030712, 0.96)
    this.overlay.fillRoundedRect(x, y, width, 264, 8)
    this.overlay.fillStyle(fighter.tint, 0.22)
    this.overlay.fillRect(x + 8, y + 8, width - 16, 54)
    this.overlay.lineStyle(2, fighter.trim, 0.88)
    this.overlay.strokeRoundedRect(x, y, width, 264, 8)
    this.overlay.fillStyle(0xfef3c7, 1)
    this.overlay.fillRect(flip ? x + width - 92 : x + 18, y + 22, 74, 8)
    this.overlay.fillStyle(fighter.trim, 1)
    this.overlay.fillRect(flip ? x + width - 122 : x + 18, y + 44, 104, 6)

    this.drawStatBars(x + 28, y + 82, fighter.stats, fighter.trim)
    labelText.setText(`${label}\n${fighter.name}`)
    labelText.setPosition(x + width / 2, y + 20)
    labelText.setVisible(true)
  }

  private createSelectLabel(): Phaser.GameObjects.Text {
    const labelText = this.add.text(0, 0, '', {
      align: 'center',
      color: '#fff7ad',
      fontFamily: 'Consolas, monospace',
      fontSize: '16px',
      fontStyle: 'bold',
      stroke: '#020617',
      strokeThickness: 4,
    })
    labelText.setOrigin(0.5, 0)
    labelText.setDepth(43)
    labelText.setVisible(false)
    return labelText
  }

  private drawStatBars(x: number, y: number, stats: [number, number, number], color: number): void {
    for (let i = 0; i < stats.length; i += 1) {
      this.overlay.fillStyle(0x111827, 1)
      this.overlay.fillRect(x, y + i * 24, 172, 10)
      this.overlay.fillStyle(color, 1)
      this.overlay.fillRect(x, y + i * 24, Math.floor(172 * (stats[i] / 100)), 10)
      this.overlay.lineStyle(1, 0xfef3c7, 0.5)
      this.overlay.strokeRect(x, y + i * 24, 172, 10)
    }
  }

  private drawFlowOverlay(): void {
    this.overlay.clear()
    this.selectInfo.setText('')
    this.selectP1.setVisible(false)
    this.selectP2.setVisible(false)
    this.selectLabelP1.setVisible(false)
    this.selectLabelP2.setVisible(false)

    if (this.mode === 'intro') {
      this.overlay.fillStyle(0x020617, 0.18)
      this.overlay.fillRect(0, 0, GAME_WIDTH, GAME_HEIGHT)
    }

    if (this.mode === 'roundOver' || this.mode === 'matchOver') {
      this.overlay.fillStyle(0x020617, 0.4)
      this.overlay.fillRect(0, 0, GAME_WIDTH, GAME_HEIGHT)
      if (this.mode === 'matchOver') {
        const winner = this.matchWinner === 'p1' ? this.playerOne.name : this.matchWinner === 'p2' ? this.playerTwo.name : 'DRAW'
        this.selectInfo.setText(`${winner} TAKES THE SET\nENTER / CLICK RETURNS TO CHARACTER SELECT`)
      }
    }
  }

  private renderFighter(fighter: Fighter, time: number): void {
    const frameKey = this.spriteFrameKey(fighter)
    if (!this.textures.exists(frameKey)) {
      fighter.sprite.setVisible(false)
      return
    }

    const walkBob = fighter.state === 'walk' ? Math.sin(time / 70) * 4 : 0
    const jumpBob = fighter.state === 'jump' ? -4 : 0
    const spriteY = Math.round(fighter.y + walkBob + jumpBob)

    fighter.shadow.clear()
    fighter.shadow.setDepth(fighter.id === 'p1' ? 11 : 12)
    fighter.shadow.fillStyle(0x000000, 0.32)
    const down = fighter.state === 'knockdown' || fighter.state === 'ko'
    fighter.shadow.fillEllipse(Math.round(fighter.x), GROUND_Y + 8, down ? 104 : fighter.state === 'jump' ? 54 : 74, down ? 12 : 14)

    fighter.sprite.setVisible(true)
    if (fighter.sprite.texture.key !== frameKey) {
      fighter.sprite.setTexture(frameKey)
    }
    fighter.sprite.setPosition(Math.round(fighter.x), spriteY)
    fighter.sprite.setDepth(fighter.id === 'p1' ? 12 : 13)
    fighter.sprite.setFlipX(fighter.facing === -1)
    fighter.sprite.setScale(fighter.spriteScale * this.spriteScaleMultiplier(fighter, frameKey))
    fighter.sprite.setAlpha(fighter.state === 'hit' && Math.floor(time / 55) % 2 === 0 ? 0.72 : 1)
    // Real knockdown/ko/wake art already draws the pose; only the legacy
    // hit/crouch fallback textures need the fake lying-down rotation.
    const usesRealStateArt =
      frameKey.includes('-ko-') || frameKey.includes('-knockdown-') || frameKey.includes('-wake-')
    fighter.sprite.setAngle(
      usesRealStateArt
        ? 0
        : fighter.state === 'ko'
          ? fighter.facing * 78
          : fighter.state === 'knockdown'
            ? fighter.facing * 82
            : fighter.state === 'wake'
              ? fighter.facing * 8
              : 0,
    )
  }

  private stateFrame(fighter: Fighter, state: keyof typeof EXTRA_STATE_FRAME_COUNTS, frame: number, fallback: string): string {
    const key = `${fighter.assetKey}-${state}-${frame}`
    return this.textures.exists(key) ? key : fallback
  }

  private spriteFrameKey(fighter: Fighter): string {
    if (fighter.state === 'attack') {
      const attackName = fighter.currentAttack ?? 'light'
      const attack = ATTACKS[attackName]
      const total = attack.startup + attack.active + attack.recovery
      const progress = Phaser.Math.Clamp(fighter.stateTime / total, 0, 0.999)
      const frameCount = ATTACK_SPRITE_FRAME_COUNTS[attack.spriteState]
      const frame =
        fighter.stateTime < attack.startup * 0.45
          ? 0
          : fighter.stateTime < attack.startup
            ? 1
            : fighter.stateTime < attack.startup + attack.active
              ? 2
              : Math.min(frameCount - 1, 3 + Math.floor(progress * (frameCount - 3)))
      const key = `${fighter.assetKey}-${attack.spriteState}-${frame}`
      if (this.textures.exists(key)) {
        return key
      }
      const legacy = attack.spriteState === 'super' ? 'kick' : attack.spriteState === 'throw' || attack.spriteState === 'special' ? 'heavy' : 'light'
      return `${fighter.assetKey}-${legacy}-${Math.min(frame, 4)}`
    }

    if (fighter.state === 'block') {
      const frame = fighter.blockFlash > 0 ? 2 : Math.min(1, Math.floor(fighter.stateTime / 90))
      return this.stateFrame(fighter, 'block', frame, `${fighter.assetKey}-idle-1`)
    }

    if (fighter.state === 'ko') {
      const frame = Math.min(3, Math.floor(fighter.stateTime / 110))
      return this.stateFrame(fighter, 'ko', frame, `${fighter.assetKey}-hit-1`)
    }

    if (fighter.state === 'knockdown') {
      const frame = Math.min(4, Math.floor(fighter.stateTime / 130))
      return this.stateFrame(fighter, 'knockdown', frame, `${fighter.assetKey}-hit-1`)
    }

    if (fighter.state === 'wake') {
      const frame = Math.min(3, Math.floor(fighter.stateTime / 65))
      return this.stateFrame(fighter, 'wake', frame, `${fighter.assetKey}-crouch-1`)
    }

    if (fighter.state === 'victory') {
      const frame = Math.min(4, Math.floor(fighter.stateTime / 130))
      return this.stateFrame(fighter, 'victory', frame, `${fighter.assetKey}-idle-0`)
    }

    if (fighter.state === 'idle') {
      return `${fighter.assetKey}-idle-${Math.floor(fighter.stateTime / 115) % SPRITE_FRAME_COUNTS.idle}`
    }

    if (fighter.state === 'walk') {
      return `${fighter.assetKey}-run-${Math.floor(fighter.stateTime / 58) % MOVEMENT_FRAME_COUNTS.run}`
    }

    if (fighter.state === 'crouch') {
      return `${fighter.assetKey}-crouch-${Math.floor(fighter.stateTime / 150) % SPRITE_FRAME_COUNTS.crouch}`
    }

    if (fighter.state === 'jump') {
      const frame = this.jumpFrame(fighter)
      return `${fighter.assetKey}-jump-bent-${frame}`
    }

    if (fighter.state === 'landing') {
      const frame = Math.min(2, Math.floor(fighter.stateTime / 45))
      return this.stateFrame(fighter, 'landing', frame, `${fighter.assetKey}-jump-bent-${fighter.stateTime < 120 ? 5 : 0}`)
    }

    if (fighter.state === 'hit') {
      const frame = Math.min(HIT_REACTION_FRAME_COUNT - 1, Math.floor(fighter.stateTime / 80))
      if (fighter.hitReaction === 'crouch') {
        return `${fighter.assetKey}-crouch-hit-${frame}`
      }

      if (fighter.hitReaction === 'air') {
        return `${fighter.assetKey}-air-hit-${frame}`
      }

      return `${fighter.assetKey}-hit-${Math.min(2, Math.floor(fighter.stateTime / 95))}`
    }

    return `${fighter.assetKey}-idle-0`
  }

  private jumpFrame(fighter: Fighter): number {
    if (fighter.stateTime < 80) {
      return 0
    }

    if (fighter.vy < -610) {
      return 1
    }

    if (fighter.vy < -190) {
      return 2
    }

    if (fighter.vy < 180) {
      return 3
    }

    return 4
  }

  private spriteScaleMultiplier(fighter: Fighter, frameKey: string): number {
    const multipliers = MOVEMENT_SCALE_MULTIPLIERS[fighter.assetKey] ?? DEFAULT_MOVEMENT_SCALE

    if (frameKey.includes('-run-')) {
      return multipliers.run
    }

    if (frameKey.includes('-jump-tuck-')) {
      return multipliers.jumpTuck
    }

    return 1
  }

  private unlockAudio(): void {
    if (this.audioContext) {
      if (this.audioContext.state === 'suspended') {
        void this.audioContext.resume()
      }
      return
    }

    const audioWindow = window as typeof window & { webkitAudioContext?: typeof AudioContext }
    const Context = window.AudioContext || audioWindow.webkitAudioContext
    if (!Context) {
      return
    }
    this.audioContext = new Context()
  }

  private playMusic(track: MusicTrack | null): void {
    const fullKey = track ? `music-${track}` : ''
    if (this.musicKey === fullKey) {
      return
    }
    this.music?.stop()
    this.music?.destroy()
    this.music = null
    this.musicKey = fullKey
    if (!track || !this.cache.audio.exists(fullKey)) {
      return
    }
    this.music = this.sound.add(fullKey, { loop: track !== 'victory', volume: track === 'fight' ? 0.3 : 0.38 })
    this.music.play()
  }

  private playSound(kind: SoundKind): void {
    if (this.cache.audio.exists(`sfx-${kind}`)) {
      this.sound.play(`sfx-${kind}`, { volume: SFX_VOLUMES[kind] })
      return
    }

    if (!this.audioContext) {
      return
    }

    const specs: Record<typeof kind, [number, number, OscillatorType, number, number]> = {
      menu: [520, 0.045, 'square', 0.035, 120],
      round: [220, 0.12, 'square', 0.045, 180],
      start: [640, 0.14, 'square', 0.045, 260],
      jump: [340, 0.07, 'triangle', 0.025, 180],
      dash: [170, 0.045, 'sawtooth', 0.025, -40],
      hit: [110, 0.075, 'sawtooth', 0.06, -55],
      block: [260, 0.055, 'square', 0.035, -120],
      throw: [90, 0.14, 'sawtooth', 0.07, -38],
      ko: [80, 0.24, 'sawtooth', 0.065, -50],
      special: [720, 0.09, 'triangle', 0.04, 240],
      super: [180, 0.2, 'sawtooth', 0.055, 520],
      superHit: [70, 0.2, 'sawtooth', 0.08, -30],
      deny: [120, 0.04, 'square', 0.025, -20],
    }
    const [frequency, duration, type, volume, slide] = specs[kind]
    const now = this.audioContext.currentTime
    const oscillator = this.audioContext.createOscillator()
    const gain = this.audioContext.createGain()
    oscillator.type = type
    oscillator.frequency.setValueAtTime(frequency, now)
    oscillator.frequency.exponentialRampToValueAtTime(Math.max(30, frequency + slide), now + duration)
    gain.gain.setValueAtTime(volume, now)
    gain.gain.exponentialRampToValueAtTime(0.0001, now + duration)
    oscillator.connect(gain)
    gain.connect(this.audioContext.destination)
    oscillator.start(now)
    oscillator.stop(now + duration)
  }

}
