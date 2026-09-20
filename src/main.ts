import Phaser from 'phaser'
import './style.css'
import { FightScene } from './game/FightScene'
import { mountTouchControls } from './game/touchUI'

declare global {
  interface Window {
    __fightingGame?: Phaser.Game
  }
}

const rendererType = new URLSearchParams(window.location.search).get('renderer') === 'canvas' ? Phaser.CANVAS : Phaser.AUTO

const config: Phaser.Types.Core.GameConfig = {
  type: rendererType,
  parent: 'app',
  width: 960,
  height: 540,
  backgroundColor: '#10172a',
  pixelArt: true,
  roundPixels: true,
  scale: {
    mode: Phaser.Scale.FIT,
    autoCenter: Phaser.Scale.CENTER_BOTH,
  },
  scene: [FightScene],
}

const game = new Phaser.Game(config)

mountTouchControls()

if (import.meta.env.DEV) {
  window.__fightingGame = game
}
