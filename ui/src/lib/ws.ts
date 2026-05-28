type ArasWsEvent = {
  event: string;
  resource?: string;
  id?: string | number;
};

let socket: WebSocket | null = null;

export function connectArasWebSocket() {
  if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) return socket;

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  socket = new WebSocket(`${protocol}//${window.location.host}/api/v1/ws`);

  socket.onmessage = (message) => {
    try {
      const detail = JSON.parse(message.data) as ArasWsEvent;
      window.dispatchEvent(new CustomEvent('aras:record-event', { detail }));
    } catch {
      window.dispatchEvent(new CustomEvent('aras:record-event', { detail: { event: 'message' } }));
    }
  };

  socket.onclose = () => {
    socket = null;
    window.setTimeout(connectArasWebSocket, 3000);
  };

  return socket;
}
