// Relays Spilled progress to the loopback launcher service (content scripts cannot reach it directly).
const API = 'http://127.0.0.1:8765';
const post = (path, body) => fetch(API + path, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)});

chrome.runtime.onMessage.addListener((msg, sender, reply) => {
  if (msg && msg.type === 'media' && sender.tab && (msg.action === 'pause' || msg.action === 'resume')) {
    chrome.tabs.sendMessage(sender.tab.id, {type: 'media-all', action: msg.action}).catch(() => {});
    return;
  }
  let host = '';
  try { host = new URL(sender.url || '').hostname; } catch {}
  if (host !== 'spilled.kaooffline.top' || !msg || typeof msg !== 'object') return;
  if (msg.type === 'continue' && Array.isArray(msg.items)) {
    post('/api/spilled/continue', {items: msg.items}).catch(() => {});
    return;
  }
  if (msg.type === 'pending') {
    post('/api/spilled/pending', {}).then(r => r.json()).then(reply, () => reply({}));
    return true;
  }
});
