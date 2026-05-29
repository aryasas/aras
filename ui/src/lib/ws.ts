import { useAuthStore } from '../store/authStore'

type ArasWsEvent = {
  event: string;
  resource?: string;
  id?: string | number;
};

let socket: WebSocket | null = null;
let reconnectTimer: number | null = null;
let reconnectDelay = 1000;

function clearReconnect() {
  if (reconnectTimer !== null) {
    window.clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }
}

function getWsUrl(token: string) {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${window.location.host}/api/v1/ws?token=${encodeURIComponent(token)}`;
}

export function connectArasWebSocket() {
  const token = useAuthStore.getState().token;
  if (!token) return null;
  if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) return socket;

  clearReconnect();
  socket = new WebSocket(getWsUrl(token));

  socket.onopen = () => {
    reconnectDelay = 1000;
  };

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
    if (!useAuthStore.getState().token) return;
    const delay = reconnectDelay;
    reconnectDelay = Math.min(reconnectDelay * 2, 30000);
    reconnectTimer = window.setTimeout(() => {
      reconnectTimer = null;
      connectArasWebSocket();
    }, delay);
  };

  return socket;
}

export function disconnectArasWebSocket() {
  clearReconnect();
  const current = socket;
  socket = null;
  current?.close();
}
