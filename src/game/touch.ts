import Phaser from 'phaser'

export type ControlName =
  | 'left' | 'right' | 'up' | 'down'
  | 'block' | 'light' | 'heavy' | 'kick'

export type TouchPlayer = 'p1' | 'p2'

/**
 * A single bindable control. Keyboard state lives on the Phaser key;
 * touch state lives alongside it so both feed the same reads.
 */
export type Control = {
  key: Phaser.Input.Keyboard.Key
  touchDown: boolean
  touchJust: boolean
}

const registry = new Map<string, Control>()

const slot = (player: TouchPlayer, name: ControlName): string => `${player}:${name}`

export function registerControl(player: TouchPlayer, name: ControlName, control: Control): void {
  registry.set(slot(player, name), control)
}

export function pressControl(player: TouchPlayer, name: ControlName): void {
  const control = registry.get(slot(player, name))
  if (!control) return
  // Only raise the edge flag on a real transition, so holding a button
  // does not re-trigger single-fire actions every frame.
  if (!control.touchDown) control.touchJust = true
  control.touchDown = true
}

export function releaseControl(player: TouchPlayer, name: ControlName): void {
  const control = registry.get(slot(player, name))
  if (!control) return
  control.touchDown = false
}

/** Clears every held control. Used when the overlay loses pointer capture. */
export function releaseAll(): void {
  for (const control of registry.values()) control.touchDown = false
}

/** Reads and consumes the touch edge flag, mirroring Phaser's JustDown. */
export function consumeTouchJust(control: Control): boolean {
  if (!control.touchJust) return false
  control.touchJust = false
  return true
}

if (import.meta.env.DEV) {
  ;(window as unknown as Record<string, unknown>).__ndTouch = {
    pressControl,
    releaseControl,
    releaseAll,
  }
}
