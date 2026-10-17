(() => {
  'use strict';
  if (location.pathname !== '/') return;
  const main = document.getElementById('main');
  if (!main || !main.querySelector('.board')) return;
  const status = document.createElement('p');
  status.setAttribute('role', 'status');
  status.className = 'refresh-status';
  main.before(status);
  const normal = 'Updates every 15 seconds while this tab is visible.';
  status.textContent = normal;
  let timer, controller, lastHTML = main.innerHTML;

  // Reuse keyed cards even when they move columns. Keep native disclosure state.
  function patch(current, incoming, keyed) {
    if (current.nodeType === Node.TEXT_NODE) {
      if (current.data !== incoming.data) current.data = incoming.data;
      return;
    }
    if (current.nodeType !== Node.ELEMENT_NODE) return;
    for (const attr of [...current.attributes]) {
      if (current.tagName === 'DETAILS' && attr.name === 'open') continue;
      if (!incoming.hasAttribute(attr.name)) current.removeAttribute(attr.name);
    }
    for (const attr of incoming.attributes) {
      if (current.tagName === 'DETAILS' && attr.name === 'open') continue;
      if (current.getAttribute(attr.name) !== attr.value) current.setAttribute(attr.name, attr.value);
    }
    let cursor = current.firstChild;
    for (const next of [...incoming.childNodes]) {
      let node = next.id ? keyed.get(next.id) : cursor;
      if (!node || node.nodeType !== next.nodeType || node.nodeName !== next.nodeName ||
          (node.id || '') !== (next.id || '')) node = next.cloneNode(true);
      if (node !== cursor) current.insertBefore(node, cursor);
      patch(node, next, keyed);
      cursor = node.nextSibling;
    }
    while (cursor) { const next = cursor.nextSibling; cursor.remove(); cursor = next; }
  }

  function schedule() {
    clearTimeout(timer);
    if (!document.hidden) timer = setTimeout(refresh, 15000);
  }
  async function refresh() {
    clearTimeout(timer);
    if (document.hidden || controller) return;
    const active = new AbortController();
    controller = active;
    const timeout = setTimeout(() => active.abort(), 10000);
    try {
      const response = await fetch('/', {cache: 'no-store', signal: active.signal});
      if (!response.ok) throw new Error('HTTP ' + response.status);
      const page = new DOMParser().parseFromString(await response.text(), 'text/html');
      const incoming = page.getElementById('main');
      if (!incoming?.querySelector('.board')) throw new Error('Invalid dashboard');
      if (document.hidden) return;
      if (incoming.innerHTML !== lastHTML) {
        const focused = document.activeElement;
        const x = scrollX, y = scrollY;
        const keyed = new Map([...main.querySelectorAll('[id]')].map(node => [node.id, node]));
        patch(main, incoming, keyed);
        // A moved card can temporarily lose focus while detached from its column.
        if (focused?.isConnected && document.activeElement !== focused) focused.focus({preventScroll: true});
        window.scrollTo({left: x, top: y, behavior: 'instant'});
        lastHTML = incoming.innerHTML;
      }
      status.textContent = normal;
    } catch (error) {
      if (!document.hidden) status.textContent = 'Refresh unavailable — showing the last loaded data. Retrying in 15 seconds.';
    } finally {
      clearTimeout(timeout);
      controller = null;
      schedule();
    }
  }
  document.addEventListener('visibilitychange', () => {
    clearTimeout(timer);
    if (document.hidden) controller?.abort();
    else schedule();
  });
  // Manual refresh also preserves the current reading position and expanded cards.
  main.addEventListener('click', event => {
    if (event.target.closest('a.button[href="/"]')) { event.preventDefault(); refresh(); }
  });
  schedule();
})();
