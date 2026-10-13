import { connect, exit, dispose, reportError } from '@dlc/sdk';
import { mountRhythm } from './game/game.js';
import template from './game/template.html?raw';
import styles from './game/style.css?raw';

const lifetime = new AbortController();
let controller;
try {
  await connect('twilight-rhythm');
  const root = document.querySelector('#game-root').attachShadow({ mode: 'open' });
  root.innerHTML = template;
  const style = document.createElement('style'); style.textContent = styles; root.prepend(style);
  controller = await mountRhythm(root, { signal: lifetime.signal, onExit: () => void exit().catch(reportError) });
} catch (error) { reportError(error); }
window.addEventListener('pagehide', () => { lifetime.abort(); controller?.destroy(); dispose(); }, { once: true });
