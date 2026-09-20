import './touch.css'
import { pressControl, releaseAll, releaseControl, type ControlName } from './touch'

type ButtonSpec = { name: ControlName; label: string; round?: boolean }

const PAD: ButtonSpec[] = [
  { name: 'up', label: '▲' },
  { name: 'left', label: '◀' },
  { name: 'down', label: '▼' },
  { name: 'right', label: '▶' },
]

const CLUSTER: ButtonSpec[] = [
  { name: 'light', label: 'LP', round: true },
  { name: 'heavy', label: 'HP', round: true },
  { name: 'kick', label: 'K', round: true },
  { name: 'block', label: 'BLK', round: true },
]

export function isTouchDevice(): boolean {
  return window.matchMedia('(pointer: coarse)').matches
}

function makeButton(spec: ButtonSpec): HTMLButtonElement {
  const button = document.createElement('button')
  button.type = 'button'
  button.className = spec.round ? 'nd-btn round' : 'nd-btn'
  button.textContent = spec.label
  button.dataset.ndControl = spec.name
  button.setAttribute('aria-label', spec.name)

  const press = (event: PointerEvent): void => {
    event.preventDefault()
    // Touch pointers get implicit capture on pointerdown, which suppresses
    // pointerleave until the finger lifts. Releasing it makes boundary
    // events fire normally, so sliding off a button releases it and
    // sliding onto another can press it.
    if (button.hasPointerCapture?.(event.pointerId)) {
      button.releasePointerCapture(event.pointerId)
    }
    button.dataset.pressed = 'true'
    pressControl('p1', spec.name)
  }
  const release = (event: PointerEvent): void => {
    event.preventDefault()
    delete button.dataset.pressed
    releaseControl('p1', spec.name)
  }

  button.addEventListener('pointerdown', press)
  button.addEventListener('pointerup', release)
  button.addEventListener('pointercancel', release)
  button.addEventListener('pointerleave', release)
  // Stop the browser turning a rapid tap into scroll or zoom.
  button.addEventListener('contextmenu', (event) => event.preventDefault())

  return button
}

/**
 * Mounts player-one touch controls. Returns null on mouse-only devices,
 * where the overlay would only occlude the fight.
 */
export function mountTouchControls(root: HTMLElement = document.body): HTMLElement | null {
  if (!isTouchDevice()) return null
  if (document.querySelector('[data-nd-overlay]')) return null

  const overlay = document.createElement('div')
  overlay.className = 'nd-touch'
  overlay.dataset.ndOverlay = 'p1'

  const pad = document.createElement('div')
  pad.className = 'nd-pad'
  for (const spec of PAD) pad.appendChild(makeButton(spec))

  const spacer = document.createElement('div')

  const cluster = document.createElement('div')
  cluster.className = 'nd-cluster'
  for (const spec of CLUSTER) cluster.appendChild(makeButton(spec))

  overlay.append(pad, spacer, cluster)
  root.appendChild(overlay)

  // A backgrounded tab never delivers pointerup; clear held controls so the
  // fighter does not keep walking on return.
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) releaseAll()
  })
  window.addEventListener('blur', releaseAll)

  return overlay
}
