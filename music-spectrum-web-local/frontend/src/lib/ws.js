/**
 * Lightweight WebSocket client that auto-reconnects.
 */
export function createWS(onMessage) {
  let ws;
  let closed = false;
  let timer;

  function connect() {
    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws';
    ws = new WebSocket(`${proto}://${window.location.host}/ws`);
    ws.onmessage = (e) => {
      try {
        onMessage(JSON.parse(e.data));
      } catch {
        /* ignore */
      }
    };
    ws.onclose = () => {
      if (closed) return;
      timer = setTimeout(connect, 2000);
    };
    ws.onerror = () => ws.close();
  }
  connect();

  return () => {
    closed = true;
    clearTimeout(timer);
    try { ws && ws.close(); } catch { /* ignore */ }
  };
}
