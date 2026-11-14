// Bytecek switches between Home and an app without minimizing it (minimize/restore
// glitches on this hardware), so the app's media is paused while Home is in front:
//   Ctrl+Alt+Shift+F12 (sent by home.sh)       -> pause what is playing
//   Ctrl+Alt+Shift+F11 (sent when app returns)  -> resume what we paused
(() => {
  let paused = [];
  function act(action) {
    if (action === 'pause') {
      paused = [...document.querySelectorAll('video,audio')].filter((m) => !m.paused && !m.ended);
      paused.forEach((m) => m.pause());
    } else if (action === 'resume') {
      paused.forEach((m) => { if (m.isConnected) m.play().catch(() => {}); });
      paused = [];
    }
  }
  window.addEventListener('keydown', (e) => {
    if (!(e.ctrlKey && e.altKey && e.shiftKey) || (e.key !== 'F12' && e.key !== 'F11')) return;
    e.preventDefault();
    e.stopImmediatePropagation();
    const action = e.key === 'F12' ? 'pause' : 'resume';
    act(action);
    // Players often live in iframes: ask every frame of this tab to do the same.
    try { chrome.runtime.sendMessage({type: 'media', action}).catch?.(() => {}); } catch {}
  }, true);
  chrome.runtime.onMessage.addListener((msg) => { if (msg && msg.type === 'media-all') act(msg.action); });
})();
