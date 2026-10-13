// Game API v1. Safe to import from a Worker: browser state is accessed in connect().
let values = Object.create(null), api = '', standaloneKey = '', dirty = false, timer, poll;
let chain = Promise.resolve(), generation = 0, outputDevice = '', originalAudioContext;
const contexts = new Set();

export const storage = {
  getItem(key) { return typeof values[key] === 'string' ? values[key] : null; },
  setItem(key, value) { values[key] = String(value); dirty = true; generation++; clearTimeout(timer); timer = setTimeout(() => void flush().catch(reportError), 150); },
  removeItem(key) { delete values[key]; dirty = true; generation++; void flush().catch(reportError); },
};

export async function flush() {
  clearTimeout(timer);
  chain = chain.catch(() => {}).then(async () => {
    if (!dirty) return;
    const revision = generation, body = JSON.stringify(values);
    if (new TextEncoder().encode(body).length > 8 * 1024 * 1024) throw new Error('存档超过 8 MiB，请减少导入曲目后重试。');
    if (api) {
      const response = await fetch(api + 'save', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body });
      if (!response.ok) throw new Error('存档保存失败：' + await response.text());
    } else localStorage.setItem(standaloneKey, body);
    if (revision === generation) dirty = false;
  });
  return chain;
}

async function applyDevice(context) {
  if (context.state !== 'closed' && context.setSinkId) {
    try { await context.setSinkId(outputDevice); }
    catch { /* Device IDs can be origin-specific; retain system routing. */ }
  }
}
function wrapAudio() {
  const Original = window.AudioContext || window.webkitAudioContext;
  if (!Original) return;
  originalAudioContext = Original;
  function GameAudioContext(...args) {
    const context = new Original(...args); contexts.add(context); void applyDevice(context);
    context.addEventListener('statechange', () => { if (context.state === 'closed') contexts.delete(context); });
    return context;
  }
  GameAudioContext.prototype = Original.prototype; Object.setPrototypeOf(GameAudioContext, Original);
  window.AudioContext = GameAudioContext;
  if (window.webkitAudioContext) window.webkitAudioContext = GameAudioContext;
}

export async function connect(id) {
  standaloneKey = 'lingchat-dlc:' + id;
  const token = location.pathname.split('/')[1];
  if (location.hostname === '127.0.0.1' && /^[a-f0-9]{32}$/.test(token)) api = `/${token}/_host/`;
  if (api) {
    const response = await fetch(api + 'save');
    if (!response.ok) throw new Error('无法读取 DLC 存档。');
    const saved = await response.json();
    if (!saved || Array.isArray(saved) || typeof saved !== 'object') throw new Error('DLC 存档格式无效。');
    values = Object.assign(Object.create(null), saved);
    await refreshPreferences(); poll = setInterval(() => void refreshPreferences().catch(() => {}), 3000);
  } else {
    const saved = JSON.parse(localStorage.getItem(standaloneKey) || '{}');
    values = Object.assign(Object.create(null), saved);
  }
  wrapAudio();
  window.addEventListener('dlc-before-close', beforeClose);
  document.addEventListener('visibilitychange', visibility);
}
async function refreshPreferences() {
  const response = await fetch(api + 'config'); if (!response.ok) return;
  const config = await response.json(); if (config.api_version !== 1) throw new Error('宿主 API 版本不兼容。');
  document.documentElement.lang = config.preferences.locale || 'zh-CN';
  const next = config.preferences.output_device || '';
  if (next !== outputDevice) { outputDevice = next; for (const context of contexts) void applyDevice(context); }
}
function beforeClose() { void exit().catch(reportError); }
function visibility() { if (document.hidden) void flush().catch(reportError); }
export async function exit() {
  await flush();
  if (api) { const response = await fetch(api + 'exit', { method: 'POST' }); if (!response.ok) throw new Error('退出失败，请关闭窗口。'); }
  else { dispose(); document.querySelector('#game-root').innerHTML = '<p style="padding:30px;color:white">游戏已退出。刷新页面可重新开始。</p>'; }
}
export function dispose() {
  clearInterval(poll); clearTimeout(timer);
  window.removeEventListener('dlc-before-close', beforeClose); document.removeEventListener('visibilitychange', visibility);
  for (const context of contexts) void context.close().catch(() => {}); contexts.clear();
  if (originalAudioContext) { window.AudioContext = originalAudioContext; if (window.webkitAudioContext) window.webkitAudioContext = originalAudioContext; }
}
export function reportError(error) {
  console.error(error);
  let notice = document.querySelector('#dlc-error');
  if (!notice) {
    notice = document.createElement('button'); notice.id = 'dlc-error';
    notice.style.cssText = 'position:fixed;z-index:99999;left:12px;right:12px;top:12px;background:#502030;color:white;border:1px solid #ff9fbb;border-radius:8px;padding:12px;cursor:pointer';
    notice.onclick = () => void flush().then(() => notice.remove()).catch(reportError); document.body.append(notice);
  }
  notice.textContent = String(error) + '（点击重试保存）';
}
