import { expect, test, type Page } from '@playwright/test'

async function startMatch(page: Page): Promise<void> {
  await page.goto('/')
  await page.waitForFunction(() => Boolean((window as any).__fightingGame))

  // Advance character select into the fight. FightScene#create() preloads
  // sprite atlases for eleven fighters before it binds input, which can take
  // longer than a fixed delay depending on machine load. Retry the Enter
  // press until the mode actually leaves 'select' instead of trusting a
  // single fixed wait.
  await expect
    .poll(
      async () => {
        const mode = await page.evaluate(
          () => (window as any).__fightingGame.scene.keys.FightScene.mode,
        )
        if (mode === 'select') {
          await page.keyboard.press('Enter')
        }
        return mode
      },
      { timeout: 20_000, intervals: [200, 500] },
    )
    .not.toBe('select')

  await page.waitForFunction(() => {
    const scene = (window as any).__fightingGame.scene.keys.FightScene
    return scene && scene.mode === 'fight'
  }, undefined, { timeout: 30_000 })
}

function p1X(page: Page): Promise<number> {
  return page.evaluate(() => (window as any).__fightingGame.scene.keys.FightScene.playerOne.x)
}

test('touch press moves player one right', async ({ page }) => {
  await startMatch(page)
  const before = await p1X(page)

  await page.evaluate(() => (window as any).__ndTouch.pressControl('p1', 'right'))
  await page.waitForTimeout(600)
  await page.evaluate(() => (window as any).__ndTouch.releaseControl('p1', 'right'))

  const after = await p1X(page)
  expect(after).toBeGreaterThan(before)
})

test('touch release stops player one', async ({ page }) => {
  await startMatch(page)

  await page.evaluate(() => (window as any).__ndTouch.pressControl('p1', 'right'))
  await page.waitForTimeout(400)
  await page.evaluate(() => (window as any).__ndTouch.releaseControl('p1', 'right'))
  await page.waitForTimeout(200)

  const settled = await p1X(page)
  await page.waitForTimeout(400)
  const later = await p1X(page)
  expect(Math.abs(later - settled)).toBeLessThan(2)
})

test('keyboard still moves player one', async ({ page }) => {
  await startMatch(page)
  const before = await p1X(page)

  await page.keyboard.down('d')
  await page.waitForTimeout(600)
  await page.keyboard.up('d')

  const after = await p1X(page)
  expect(after).toBeGreaterThan(before)
})

test.describe('control overlay', () => {
  test.use({ hasTouch: true, isMobile: true, viewport: { width: 390, height: 844 } })

  test('overlay renders on touch devices and drives the fighter', async ({ page }) => {
    await startMatch(page)

    const right = page.locator('[data-nd-control="right"]')
    await expect(right).toBeVisible()

    const before = await p1X(page)
    await right.dispatchEvent('pointerdown')
    await page.waitForTimeout(600)
    await right.dispatchEvent('pointerup')
    const after = await p1X(page)

    expect(after).toBeGreaterThan(before)
  })

  test('sliding a touch off a control releases it without lifting', async ({ page }) => {
    // Synthetic dispatchEvent('pointerdown') cannot reproduce this bug class:
    // real touch pointers get *implicit pointer capture* on touchstart, which
    // suppresses pointerleave/pointerout until the finger actually lifts.
    // Only genuine touch input via CDP exercises that capture behavior, so
    // this drives the button with Input.dispatchTouchEvent instead.
    await startMatch(page)

    const right = page.locator('[data-nd-control="right"]')
    const box = await right.boundingBox()
    if (!box) throw new Error('right control has no bounding box')
    const x = box.x + box.width / 2
    const y = box.y + box.height / 2

    const client = await page.context().newCDPSession(page)

    const before = await p1X(page)
    await client.send('Input.dispatchTouchEvent', {
      type: 'touchStart',
      touchPoints: [{ x, y }],
    })
    await page.waitForTimeout(300)
    expect(await right.getAttribute('data-pressed')).toBe('true')

    const whileHeld = await p1X(page)
    expect(whileHeld).toBeGreaterThan(before)

    // Slide the same touch straight up and off the button, without a
    // touchend. Ten steps comfortably clears the 52px button plus its 4px
    // grid gap.
    for (let i = 1; i <= 10; i++) {
      await client.send('Input.dispatchTouchEvent', {
        type: 'touchMove',
        touchPoints: [{ x, y: y - i * 25 }],
      })
      await page.waitForTimeout(20)
    }
    await page.waitForTimeout(200)

    expect(await right.getAttribute('data-pressed')).toBeNull()

    const afterSlide = await p1X(page)
    await page.waitForTimeout(400)
    const later = await p1X(page)
    expect(Math.abs(later - afterSlide)).toBeLessThan(2)

    await client.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] })
  })
})

test('overlay is absent on mouse-only devices', async ({ page }) => {
  await startMatch(page)
  await expect(page.locator('[data-nd-overlay]')).toHaveCount(0)
})
