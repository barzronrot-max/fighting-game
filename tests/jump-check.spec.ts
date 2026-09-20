import { expect, test, type Page } from '@playwright/test'

type RuntimeFighter = {
  blockFlash: number
  currentAttack: string | null
  grounded: boolean
  health: number
  hitReaction: string
  state: string
  stateTime: number
  sprite: { angle: number; scaleX: number; scaleY: number; texture: { key: string } }
  vy: number
  x: number
  y: number
}

type RuntimeImage = {
  displayHeight: number
  displayWidth: number
  texture: { key: string }
  visible: boolean
}

type RuntimeEffect = {
  kind: string
  sprite: { texture: { key: string }; visible: boolean }
}

type RuntimeScene = {
  checkRoundEnd: () => void
  drawHud: () => void
  effects: RuntimeEffect[]
  hudHealthFillP1: RuntimeImage
  hudHealthFrameP1: RuntimeImage
  hudHealthLagP1: RuntimeImage
  hudHealthTrackP1: RuntimeImage
  hudMeterFrameP1: RuntimeImage
  hudPortraitP1: RuntimeImage
  hudPortraitP2: RuntimeImage
  hudPipsP1: RuntimeImage[]
  hudTimerFrame: RuntimeImage
  hudTimerOnes: RuntimeImage
  hudTimerTens: RuntimeImage
  mode: string
  playerOne: RuntimeFighter
  playerTwo: RuntimeFighter
  roundTime: number
  textures: { exists: (key: string) => boolean }
  applyHit: (attacker: RuntimeFighter, defender: RuntimeFighter, attack: Record<string, unknown>) => void
  renderFighter: (fighter: RuntimeFighter, time: number) => void
  spawnImpact: (x: number, y: number, color: number, blocked: boolean) => void
  update: (time: number, delta: number) => void
  updateEffectTimers: (delta: number) => void
}

const waitForFightScene = async (page: Page) => {
  await page.waitForFunction(() => {
    const game = (window as typeof window & {
      __fightingGame?: { scene: { scenes: unknown[] } }
    }).__fightingGame

    return game?.scene.scenes.some((candidate) => {
      const scene = candidate as Partial<RuntimeScene>
      return Boolean(scene.playerOne && scene.playerTwo)
    })
  })
}

const openTestRenderer = async (page: Page) => {
  await page.goto('/?renderer=canvas')
}

test('airborne update keeps the fighter in detailed bent-knee jump frames', async ({ page }) => {
  const browserErrors: string[] = []
  page.on('console', (message) => {
    if (message.type() === 'error') {
      browserErrors.push(message.text())
    }
  })
  page.on('pageerror', (error) => browserErrors.push(error.message))

  await openTestRenderer(page)
  await waitForFightScene(page)

  const animationSamples = await page.evaluate(() => {
    const game = (window as typeof window & {
      __fightingGame?: { scene: { scenes: unknown[] } }
    }).__fightingGame
    const scene = game?.scene.scenes.find((candidate) => {
      const runtime = candidate as Partial<RuntimeScene>
      return Boolean(runtime.playerOne && runtime.playerTwo)
    }) as RuntimeScene | undefined

    if (!scene) {
      throw new Error('FightScene not found')
    }

    scene.mode = 'fight'
    const fighter = scene.playerOne
    fighter.x = 274
    fighter.y = 330
    fighter.hitReaction = 'stand'

    return [
      { label: 'takeoff', stateTime: 40, vy: -780 },
      { label: 'rising', stateTime: 130, vy: -540 },
      { label: 'apex', stateTime: 260, vy: 40 },
      { label: 'falling', stateTime: 390, vy: 360 },
    ].map((sample) => {
      fighter.grounded = false
      fighter.state = 'jump'
      fighter.stateTime = sample.stateTime
      fighter.vy = sample.vy
      scene.update(performance.now(), 16)
      scene.renderFighter(fighter, performance.now())

      return {
        grounded: fighter.grounded,
        label: sample.label,
        scaleX: fighter.sprite.scaleX,
        scaleY: fighter.sprite.scaleY,
        state: fighter.state,
        texture: fighter.sprite.texture.key,
      }
    })
  })

  for (const animationState of animationSamples) {
    expect(animationState.grounded, `${animationState.label}: ${JSON.stringify(animationState)}`).toBe(false)
    expect(animationState.scaleX, `${animationState.label}: ${JSON.stringify(animationState)}`).toBeCloseTo(0.52, 2)
    expect(animationState.scaleY, `${animationState.label}: ${JSON.stringify(animationState)}`).toBeCloseTo(0.52, 2)
    expect(animationState.state, `${animationState.label}: ${JSON.stringify(animationState)}`).toBe('jump')
    expect(animationState.texture, `${animationState.label}: ${JSON.stringify(animationState)}`).toMatch(/^kai-jump-bent-[0-4]$/)
  }

  expect(browserErrors).toEqual([])
})

test('hit reactions choose crouch and air-specific sprite poses', async ({ page }) => {
  await openTestRenderer(page)
  await waitForFightScene(page)

  const reactions = await page.evaluate(() => {
    const game = (window as typeof window & {
      __fightingGame?: { scene: { scenes: unknown[] } }
    }).__fightingGame
    const scene = game?.scene.scenes.find((candidate) => {
      const runtime = candidate as Partial<RuntimeScene>
      return Boolean(runtime.playerOne && runtime.playerTwo)
    }) as RuntimeScene | undefined

    if (!scene) {
      throw new Error('FightScene not found')
    }

    const auditHit = {
      name: 'light',
      label: 'Audit',
      spriteState: 'light',
      damage: 1,
      chip: 0,
      startup: 0,
      active: 0,
      recovery: 0,
      range: 0,
      push: 0,
      stun: 0,
      yOffset: -80,
      height: 32,
      color: 0xffffff,
      hitStop: 0,
      meterGain: 0,
    }

    const defender = scene.playerOne
    const attacker = scene.playerTwo

    defender.health = 100
    defender.state = 'crouch'
    defender.stateTime = 120
    defender.currentAttack = null
    defender.hitReaction = 'stand'
    defender.grounded = true
    defender.y = 438
    defender.vy = 0
    scene.applyHit(attacker, defender, auditHit)
    scene.renderFighter(defender, performance.now())
    const crouch = {
      grounded: defender.grounded,
      reaction: defender.hitReaction,
      state: defender.state,
      texture: defender.sprite.texture.key,
    }

    defender.health = 100
    defender.state = 'jump'
    defender.stateTime = 180
    defender.currentAttack = null
    defender.hitReaction = 'stand'
    defender.grounded = false
    defender.y = 318
    defender.vy = 260
    scene.applyHit(attacker, defender, auditHit)
    scene.renderFighter(defender, performance.now())
    const air = {
      grounded: defender.grounded,
      reaction: defender.hitReaction,
      state: defender.state,
      texture: defender.sprite.texture.key,
      vy: defender.vy,
    }

    return { crouch, air }
  })

  expect(reactions.crouch).toMatchObject({
    grounded: true,
    reaction: 'crouch',
    state: 'hit',
    texture: 'kai-crouch-hit-0',
  })
  expect(reactions.air.grounded).toBe(false)
  expect(reactions.air.reaction).toBe('air')
  expect(reactions.air.state).toBe('hit')
  expect(reactions.air.texture).toBe('kai-air-hit-0')
  expect(reactions.air.vy).toBeLessThan(0)
})

test('crouch attacks render their full-pose frames at stable fighter scale', async ({ page }) => {
  await openTestRenderer(page)
  await waitForFightScene(page)

  const samples = await page.evaluate(() => {
    const game = (window as typeof window & {
      __fightingGame?: { scene: { scenes: unknown[] } }
    }).__fightingGame
    const scene = game?.scene.scenes.find((candidate) => {
      const runtime = candidate as Partial<RuntimeScene>
      return Boolean(runtime.playerOne && runtime.playerTwo)
    }) as RuntimeScene | undefined

    if (!scene) {
      throw new Error('FightScene not found')
    }

    const auditAttack = (
      fighter: RuntimeFighter,
      attack: 'crouchPunch' | 'crouchKick',
      stateTime: number,
    ) => {
      fighter.grounded = true
      fighter.hitReaction = 'stand'
      fighter.state = 'attack'
      fighter.currentAttack = attack
      fighter.stateTime = stateTime
      fighter.vy = 0
      scene.renderFighter(fighter, performance.now())

      return {
        attack,
        scaleX: fighter.sprite.scaleX,
        scaleY: fighter.sprite.scaleY,
        texture: fighter.sprite.texture.key,
      }
    }

    return {
      kaiPunch: auditAttack(scene.playerOne, 'crouchPunch', 95),
      kaiKick: auditAttack(scene.playerOne, 'crouchKick', 125),
      novaPunch: auditAttack(scene.playerTwo, 'crouchPunch', 95),
      novaKick: auditAttack(scene.playerTwo, 'crouchKick', 125),
    }
  })

  expect(samples.kaiPunch.texture).toBe('kai-crouch-punch-2')
  expect(samples.kaiKick.texture).toBe('kai-crouch-kick-2')
  expect(samples.novaPunch.texture).toBe('nova-crouch-punch-2')
  expect(samples.novaKick.texture).toBe('nova-crouch-kick-2')

  for (const sample of [samples.kaiPunch, samples.kaiKick]) {
    expect(sample.scaleX, `${sample.attack}: ${JSON.stringify(sample)}`).toBeCloseTo(0.52, 2)
    expect(sample.scaleY, `${sample.attack}: ${JSON.stringify(sample)}`).toBeCloseTo(0.52, 2)
  }

  for (const sample of [samples.novaPunch, samples.novaKick]) {
    expect(sample.scaleX, `${sample.attack}: ${JSON.stringify(sample)}`).toBeCloseTo(0.42, 2)
    expect(sample.scaleY, `${sample.attack}: ${JSON.stringify(sample)}`).toBeCloseTo(0.42, 2)
  }
})

test('dedicated state art replaces idle/heavy/kick fallbacks', async ({ page }) => {
  await openTestRenderer(page)
  await waitForFightScene(page)

  const samples = await page.evaluate(() => {
    const game = (window as typeof window & {
      __fightingGame?: { scene: { scenes: unknown[] } }
    }).__fightingGame
    const scene = game?.scene.scenes.find((candidate) => {
      const runtime = candidate as Partial<RuntimeScene>
      return Boolean(runtime.playerOne && runtime.playerTwo)
    }) as RuntimeScene | undefined

    if (!scene) {
      throw new Error('FightScene not found')
    }

    const fighter = scene.playerOne
    const audit = (state: string, stateTime: number, currentAttack: string | null = null) => {
      fighter.grounded = true
      fighter.hitReaction = 'stand'
      fighter.blockFlash = 0
      fighter.state = state
      fighter.currentAttack = currentAttack
      fighter.stateTime = stateTime
      fighter.vy = 0
      scene.renderFighter(fighter, performance.now())
      return { angle: fighter.sprite.angle, texture: fighter.sprite.texture.key }
    }

    return {
      block: audit('block', 200),
      knockdown: audit('knockdown', 420),
      ko: audit('ko', 500),
      landing: audit('landing', 50),
      special: audit('attack', 130, 'special'),
      super: audit('attack', 180, 'super'),
      throw: audit('attack', 80, 'throw'),
      victory: audit('victory', 700),
      wake: audit('wake', 100),
    }
  })

  expect(samples.block.texture).toBe('kai-block-1')
  expect(samples.knockdown.texture).toBe('kai-knockdown-3')
  expect(samples.knockdown.angle).toBe(0)
  expect(samples.ko.texture).toBe('kai-ko-3')
  expect(samples.ko.angle).toBe(0)
  expect(samples.landing.texture).toBe('kai-landing-1')
  expect(samples.special.texture).toMatch(/^kai-special-[0-4]$/)
  expect(samples.super.texture).toMatch(/^kai-super-[0-4]$/)
  expect(samples.throw.texture).toMatch(/^kai-throw-[0-3]$/)
  expect(samples.victory.texture).toBe('kai-victory-4')
  expect(samples.wake.texture).toBe('kai-wake-1')
})

test('generated HUD assets replace old block-drawn chrome', async ({ page }) => {
  await openTestRenderer(page)
  await waitForFightScene(page)

  const hud = await page.evaluate(() => {
    const game = (window as typeof window & {
      __fightingGame?: { scene: { scenes: unknown[] } }
    }).__fightingGame
    const scene = game?.scene.scenes.find((candidate) => {
      const runtime = candidate as Partial<RuntimeScene>
      return Boolean(runtime.playerOne && runtime.playerTwo)
    }) as RuntimeScene | undefined

    if (!scene) {
      throw new Error('FightScene not found')
    }

    scene.mode = 'fight'
    scene.playerOne.wins = 1
    scene.drawHud()

    return {
      health: {
        fill: {
          texture: scene.hudHealthFillP1.texture.key,
          visible: scene.hudHealthFillP1.visible,
        },
        frame: {
          texture: scene.hudHealthFrameP1.texture.key,
          visible: scene.hudHealthFrameP1.visible,
        },
        lag: {
          texture: scene.hudHealthLagP1.texture.key,
          visible: scene.hudHealthLagP1.visible,
        },
        track: {
          texture: scene.hudHealthTrackP1.texture.key,
          visible: scene.hudHealthTrackP1.visible,
        },
      },
      meter: {
        texture: scene.hudMeterFrameP1.texture.key,
        visible: scene.hudMeterFrameP1.visible,
      },
      p1: {
        displayHeight: scene.hudPortraitP1.displayHeight,
        displayWidth: scene.hudPortraitP1.displayWidth,
        texture: scene.hudPortraitP1.texture.key,
        visible: scene.hudPortraitP1.visible,
      },
      p2: {
        displayHeight: scene.hudPortraitP2.displayHeight,
        displayWidth: scene.hudPortraitP2.displayWidth,
        texture: scene.hudPortraitP2.texture.key,
        visible: scene.hudPortraitP2.visible,
      },
      pips: scene.hudPipsP1.map((pip) => ({ texture: pip.texture.key, visible: pip.visible })),
      timer: {
        frame: scene.hudTimerFrame.texture.key,
        ones: scene.hudTimerOnes.texture.key,
        tens: scene.hudTimerTens.texture.key,
        visible: scene.hudTimerFrame.visible,
      },
    }
  })

  expect(hud.health).toEqual({
    fill: { texture: 'ui-health-fill-p1', visible: true },
    frame: { texture: 'ui-health-frame', visible: true },
    lag: { texture: 'ui-health-lag', visible: true },
    track: { texture: 'ui-health-track', visible: true },
  })
  expect(hud.meter).toEqual({ texture: 'ui-meter-frame', visible: true })
  expect(hud.p1).toEqual({
    displayHeight: 56,
    displayWidth: 56,
    texture: 'kai-portrait',
    visible: true,
  })
  expect(hud.p2).toEqual({
    displayHeight: 56,
    displayWidth: 56,
    texture: 'nova-portrait',
    visible: true,
  })
  expect(hud.pips).toEqual([
    { texture: 'ui-round-pip-full', visible: true },
    { texture: 'ui-round-pip-empty', visible: true },
  ])
  expect(hud.timer).toEqual({
    frame: 'ui-timer-frame',
    ones: 'ui-digit-9',
    tens: 'ui-digit-9',
    visible: true,
  })
})

test('generated hit VFX sprites replace square impact particles', async ({ page }) => {
  await openTestRenderer(page)
  await waitForFightScene(page)

  const vfx = await page.evaluate(() => {
    const game = (window as typeof window & {
      __fightingGame?: { scene: { scenes: unknown[] } }
    }).__fightingGame
    const scene = game?.scene.scenes.find((candidate) => {
      const runtime = candidate as Partial<RuntimeScene>
      return Boolean(runtime.playerOne && runtime.playerTwo)
    }) as RuntimeScene | undefined

    if (!scene) {
      throw new Error('FightScene not found')
    }

    scene.spawnImpact(480, 310, 0xfacc15, false)
    const initial = scene.effects.map((effect) => ({
      kind: effect.kind,
      texture: effect.sprite.texture.key,
      visible: effect.sprite.visible,
    }))
    scene.updateEffectTimers(120)
    const animated = scene.effects.map((effect) => effect.sprite.texture.key)

    return { animated, initial }
  })

  expect(vfx.initial.length).toBeGreaterThan(1)
  expect(vfx.initial[0]).toMatchObject({ kind: 'hit', texture: 'vfx-hit-0', visible: true })
  expect(vfx.animated.some((texture) => /^vfx-hit-[1-7]$/.test(texture))).toBe(true)
})

test('all fighter animation frames are loaded by the runtime', async ({ page }) => {
  await openTestRenderer(page)
  await waitForFightScene(page)

  const missing = await page.evaluate(() => {
    const game = (window as typeof window & {
      __fightingGame?: { scene: { scenes: unknown[] } }
    }).__fightingGame
    const scene = game?.scene.scenes.find((candidate) => {
      const runtime = candidate as Partial<RuntimeScene>
      return Boolean(runtime.playerOne && runtime.playerTwo)
    }) as RuntimeScene | undefined

    if (!scene) {
      throw new Error('FightScene not found')
    }

    const states: Record<string, number> = {
      'air-hit': 4,
      block: 3,
      crouch: 4,
      'crouch-hit': 4,
      'crouch-kick': 5,
      'crouch-punch': 5,
      heavy: 5,
      hit: 3,
      idle: 8,
      jump: 7,
      'jump-tuck': 6,
      kick: 5,
      knockdown: 5,
      ko: 4,
      landing: 3,
      light: 5,
      run: 5,
      special: 5,
      super: 5,
      throw: 4,
      victory: 5,
      wake: 4,
      walk: 8,
    }

    const expected: string[] = []
    for (const fighter of ['kai', 'nova', 'dragon', 'talon', 'ryu', 'kara', 'blaze', 'cyberon', 'shadow', 'luna', 'titan']) {
      for (const [state, count] of Object.entries(states)) {
        for (let index = 0; index < count; index += 1) {
          if (state === 'jump') {
            expected.push(`${fighter}-jump-bent-${index}`)
          } else {
            expected.push(`${fighter}-${state}-${index}`)
          }
        }
      }
    }

    return expected.filter((key) => !scene.textures.exists(key))
  })

  expect(missing).toEqual([])
})

test('match over accepts keyboard restart back to character select', async ({ page }) => {
  await openTestRenderer(page)
  await waitForFightScene(page)

  const matchState = await page.evaluate(() => {
    const game = (window as typeof window & {
      __fightingGame?: { scene: { scenes: unknown[] } }
    }).__fightingGame
    const scene = game?.scene.scenes.find((candidate) => {
      const runtime = candidate as Partial<RuntimeScene>
      return Boolean(runtime.playerOne && runtime.playerTwo)
    }) as RuntimeScene | undefined

    if (!scene) {
      throw new Error('FightScene not found')
    }

    scene.mode = 'fight'
    scene.roundTime = 88
    scene.playerOne.health = 72
    scene.playerTwo.health = 0
    scene.playerOne.wins = 1
    scene.playerTwo.wins = 0
    scene.checkRoundEnd()

    return {
      mode: scene.mode,
      p1Wins: scene.playerOne.wins,
      p2Health: scene.playerTwo.health,
    }
  })

  expect(matchState).toEqual({ mode: 'matchOver', p1Wins: 2, p2Health: 0 })

  await page.keyboard.press('Enter')
  await page.waitForFunction(() => {
    const game = (window as typeof window & {
      __fightingGame?: { scene: { scenes: unknown[] } }
    }).__fightingGame
    const scene = game?.scene.scenes.find((candidate) => {
      const runtime = candidate as Partial<RuntimeScene>
      return Boolean(runtime.playerOne && runtime.playerTwo)
    }) as RuntimeScene | undefined
    return scene?.mode === 'select'
  })

  const restartState = await page.evaluate(() => {
    const game = (window as typeof window & {
      __fightingGame?: { scene: { scenes: unknown[] } }
    }).__fightingGame
    const scene = game?.scene.scenes.find((candidate) => {
      const runtime = candidate as Partial<RuntimeScene>
      return Boolean(runtime.playerOne && runtime.playerTwo)
    }) as RuntimeScene | undefined

    if (!scene) {
      throw new Error('FightScene not found')
    }

    return {
      mode: scene.mode,
      p1Wins: scene.playerOne.wins,
      p2Wins: scene.playerTwo.wins,
    }
  })

  expect(restartState).toEqual({ mode: 'select', p1Wins: 2, p2Wins: 0 })

  await page.keyboard.press('Enter')
  await page.waitForFunction(() => {
    const game = (window as typeof window & {
      __fightingGame?: { scene: { scenes: unknown[] } }
    }).__fightingGame
    const scene = game?.scene.scenes.find((candidate) => {
      const runtime = candidate as Partial<RuntimeScene>
      return Boolean(runtime.playerOne && runtime.playerTwo)
    }) as RuntimeScene | undefined
    return scene?.mode === 'intro'
  })
})
