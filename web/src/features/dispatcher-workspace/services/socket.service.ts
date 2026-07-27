/**
 * DispatcherSocketService — the workspace's real-time channel.
 *
 * A production-grade WebSocket client:
 *  - lazy connect with an auth token in the query string;
 *  - automatic reconnect with exponential backoff + jitter;
 *  - heartbeat ping/pong with a liveness timeout;
 *  - a typed event emitter (`on` / `off`) plus a status observer;
 *  - graceful degradation: when the socket cannot connect, consumers fall back
 *    to TanStack Query polling — the UI never depends on the socket being up.
 *
 * The service is transport-only. It does not fabricate data; every event it
 * emits originates from the backend channel.
 */
import { env } from "@/lib/env";
import type { DispatcherEvent, SocketStatus } from "../types";

type EventHandler = (event: DispatcherEvent) => void;
type StatusHandler = (status: SocketStatus) => void;

const MAX_BACKOFF_MS = 30_000;
const BASE_BACKOFF_MS = 1_000;
const HEARTBEAT_INTERVAL_MS = 25_000;
const HEARTBEAT_TIMEOUT_MS = 10_000;

/** Resolve the socket URL from env, deriving from the origin when unset. */
export function resolveSocketUrl(token: string | null): string {
  let base = env.wsUrl;
  if (!base) {
    if (typeof window === "undefined") return "";
    const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
    base = `${proto}//${window.location.host}${env.wsDispatcherPath}`;
  }
  if (!token) return base;
  const sep = base.includes("?") ? "&" : "?";
  return `${base}${sep}token=${encodeURIComponent(token)}`;
}

export class DispatcherSocketService {
  private ws: WebSocket | null = null;
  private status: SocketStatus = "closed";
  private attempts = 0;
  private explicitlyClosed = false;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null;
  private pongTimer: ReturnType<typeof setTimeout> | null = null;
  private tokenProvider: () => string | null = () => null;

  private readonly eventHandlers = new Set<EventHandler>();
  private readonly statusHandlers = new Set<StatusHandler>();

  /** Provide a getter for the current auth token (read fresh on each connect). */
  setTokenProvider(provider: () => string | null): void {
    this.tokenProvider = provider;
  }

  getStatus(): SocketStatus {
    return this.status;
  }

  on(handler: EventHandler): () => void {
    this.eventHandlers.add(handler);
    return () => this.eventHandlers.delete(handler);
  }

  onStatus(handler: StatusHandler): () => void {
    this.statusHandlers.add(handler);
    handler(this.status);
    return () => this.statusHandlers.delete(handler);
  }

  connect(): void {
    if (typeof window === "undefined" || typeof WebSocket === "undefined") {
      this.setStatus("disabled");
      return;
    }
    if (
      this.ws &&
      (this.ws.readyState === WebSocket.OPEN ||
        this.ws.readyState === WebSocket.CONNECTING)
    ) {
      return;
    }
    this.explicitlyClosed = false;
    const url = resolveSocketUrl(this.tokenProvider());
    if (!url) {
      this.setStatus("disabled");
      return;
    }
    this.setStatus(this.attempts === 0 ? "connecting" : "reconnecting");
    try {
      this.ws = new WebSocket(url);
    } catch {
      this.scheduleReconnect();
      return;
    }
    this.ws.onopen = this.handleOpen;
    this.ws.onmessage = this.handleMessage;
    this.ws.onclose = this.handleClose;
    this.ws.onerror = this.handleError;
  }

  disconnect(): void {
    this.explicitlyClosed = true;
    this.clearTimers();
    if (this.ws) {
      this.ws.onopen = null;
      this.ws.onmessage = null;
      this.ws.onclose = null;
      this.ws.onerror = null;
      try {
        this.ws.close();
      } catch {
        /* already closing */
      }
      this.ws = null;
    }
    this.setStatus("closed");
  }

  /** Send a JSON message (best-effort; ignored when not open). */
  send(type: string, payload?: Record<string, unknown>): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, payload }));
    }
  }

  // --- internals -----------------------------------------------------------
  private handleOpen = (): void => {
    this.attempts = 0;
    this.setStatus("open");
    this.startHeartbeat();
  };

  private handleMessage = (ev: MessageEvent): void => {
    let parsed: DispatcherEvent;
    try {
      parsed = JSON.parse(ev.data as string) as DispatcherEvent;
    } catch {
      return; // ignore malformed frames
    }
    if (parsed.type === "pong") {
      this.clearPongTimer();
      return;
    }
    for (const handler of this.eventHandlers) handler(parsed);
  };

  private handleClose = (): void => {
    this.clearTimers();
    this.ws = null;
    if (this.explicitlyClosed) {
      this.setStatus("closed");
      return;
    }
    this.scheduleReconnect();
  };

  private handleError = (): void => {
    // onerror is always followed by onclose; let handleClose drive reconnect.
    try {
      this.ws?.close();
    } catch {
      /* noop */
    }
  };

  private scheduleReconnect(): void {
    this.setStatus("reconnecting");
    const backoff = Math.min(
      BASE_BACKOFF_MS * 2 ** this.attempts,
      MAX_BACKOFF_MS,
    );
    const jitter = Math.random() * 0.3 * backoff;
    this.attempts += 1;
    this.reconnectTimer = setTimeout(() => this.connect(), backoff + jitter);
  }

  private startHeartbeat(): void {
    this.clearHeartbeat();
    this.heartbeatTimer = setInterval(() => {
      if (this.ws?.readyState !== WebSocket.OPEN) return;
      this.send("ping");
      this.pongTimer = setTimeout(() => {
        // No pong in time → assume a dead connection and force a reconnect.
        try {
          this.ws?.close();
        } catch {
          /* noop */
        }
      }, HEARTBEAT_TIMEOUT_MS);
    }, HEARTBEAT_INTERVAL_MS);
  }

  private clearPongTimer(): void {
    if (this.pongTimer) {
      clearTimeout(this.pongTimer);
      this.pongTimer = null;
    }
  }

  private clearHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
    this.clearPongTimer();
  }

  private clearTimers(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.clearHeartbeat();
  }

  private setStatus(status: SocketStatus): void {
    if (this.status === status) return;
    this.status = status;
    for (const handler of this.statusHandlers) handler(status);
  }
}

/** App-wide singleton — one channel per browser tab. */
export const dispatcherSocket = new DispatcherSocketService();
