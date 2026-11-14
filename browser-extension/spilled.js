// Reads Spilled's own library state (watch progress) and reports what to continue to the launcher.
(() => {
  const WATCH = '/library/watch/';
  const num = (v) => (Number.isFinite(v) && v > 0 ? v : 0);
  const absolute = (u) => { try { const x = new URL(u, location.origin); return x.protocol === 'https:' ? x.href : ''; } catch { return ''; } };
  const order = (a, b) => (a.seasonNumber || 0) - (b.seasonNumber || 0) || (a.episodeNumber || 0) - (b.episodeNumber || 0);

  // Same account key Spilled itself uses, so only the signed-in user's library is read.
  function accountKey() {
    try {
      const c = JSON.parse(localStorage.getItem('spilled.private-node.connection.v1') || '{}');
      if (c && c.token && c.accountId) return JSON.stringify([c.nodeId || c.nodeUrl, c.accountId]);
      return localStorage.getItem('spilled-library.legacy-account.v1') ? 'guest' : '';
    } catch { return ''; }
  }

  function states() {
    const account = accountKey();
    if (!account) return [];
    const found = [];
    for (const base of ['spilled-library.state.v1', 'spilled-library.remote-base.v1']) {
      try {
        let value = JSON.parse(localStorage.getItem(`${base}:${account}`) || 'null');
        if (value && value.state && Array.isArray(value.state.shows)) value = value.state;
        if (value && Array.isArray(value.shows)) { found.push(value); break; }
      } catch {}
    }
    return found;
  }

  function entry(show, ep, label) {
    const pos = num(ep.playbackPositionSeconds);
    const dur = num(ep.playbackDurationSeconds) || num(ep.durationSeconds);
    const art = show.artwork || {};
    const series = show.mediaType !== 'movie' && (show.episodes || []).length > 1;
    const code = series && ep.seasonNumber != null ? `S${ep.seasonNumber} E${ep.episodeNumber ?? '?'}` : '';
    const title = series && typeof ep.episodeTitle === 'string' ? ep.episodeTitle : '';
    return {
      id: ep.id,
      show: String(show.title || 'Spilled'),
      label: label || [code, title].filter(Boolean).join(' \u00b7 '),
      left: dur && pos ? `${Math.max(1, Math.ceil((dur - pos) / 60))} min left` : '',
      progress: dur ? Math.round((pos / dur) * 100) : 0,
      image: absolute(ep.stillUrl || art.backdropUrl || show.backdropUrl || art.bannerUrl || show.bannerUrl || show.posterUrl || ''),
      updatedAt: num(ep.playbackUpdatedAt) || num(ep.importedAt)
    };
  }

  function collect() {
    const byId = new Map();
    for (const state of states()) {
      for (const show of state.shows) {
        const eps = (show.episodes || []).filter((e) => e && typeof e.id === 'string').sort(order);
        let inProgress = false;
        let lastDone = -1;
        let lastDoneAt = 0;
        eps.forEach((ep, i) => {
          const pos = num(ep.playbackPositionSeconds);
          const dur = num(ep.playbackDurationSeconds) || num(ep.durationSeconds);
          const done = ep.watched === true || (dur > 0 && pos >= Math.max(30, dur * 0.9));
          if (done) {
            const at = num(ep.playbackUpdatedAt);
            if (at >= lastDoneAt) { lastDoneAt = at; lastDone = i; }
          } else if (pos >= 60) {
            inProgress = true;
            const item = entry(show, ep);
            if (!byId.has(item.id) || byId.get(item.id).updatedAt < item.updatedAt) byId.set(item.id, item);
          }
        });
        // Finished an episode recently: offer the next one.
        const next = eps[lastDone + 1];
        if (!inProgress && lastDone >= 0 && lastDoneAt && next && !num(next.playbackPositionSeconds)) {
          const item = entry(show, next);
          item.label = ['Next', item.label].filter(Boolean).join(' \u00b7 ');
          item.updatedAt = lastDoneAt;
          if (!byId.has(item.id)) byId.set(item.id, item);
        }
      }
    }
    return [...byId.values()].sort((a, b) => b.updatedAt - a.updatedAt).slice(0, 12).map(({updatedAt, ...rest}) => rest);
  }

  let last = '';
  let timer;
  function report() {
    clearTimeout(timer);
    timer = setTimeout(() => {
      let items;
      try { items = collect(); } catch { return; }
      const text = JSON.stringify(items);
      if (text === last) return;
      last = text;
      chrome.runtime.sendMessage({type: 'continue', items}).catch?.(() => {});
    }, 1500);
  }

  // Home asked for a specific episode while this window was already open.
  function followJump() {
    chrome.runtime.sendMessage({type: 'pending'}).then((data) => {
      const url = data && typeof data.url === 'string' ? data.url : '';
      if (url.startsWith(location.origin + WATCH) && url !== location.href) location.assign(url);
    }).catch(() => {});
  }

  report();
  setTimeout(report, 8000);
  setInterval(report, 60000);
  window.addEventListener('spilled:library-changed', report);
  window.addEventListener('storage', report);
  window.addEventListener('focus', followJump);
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') followJump();
    else report();
  });
  followJump();
})();
