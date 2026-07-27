import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  DispatcherSocketService,
  resolveSocketUrl,
} from "../services/socket.service";
import type { DispatcherEvent, SocketStatus } from "../types";

/** Minimal controllable WebSocket stand-in. */
class FakeWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;
  static instances: FakeWebSocket[] = [];

  readyState = FakeWebSocket.CONNECTING;
  onopen: (() => void) | null = null;
  onmessage: ((ev: { data: string }) => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: (() => void) | null = null;
  sent: string[] = [];

  constructor(public url: string) {
    FakeWebSocket.instances.push(this);
  }

  send(data: string): void {
    this.sent.push(data);
  }

  close(): void {
    this.readyState = FakeWebSocket.CLOSED;
    this.onclose?.();
  }

  simulateOpen(): void {
    this.readyState = FakeWebSocket.OPEN;
    this.onopen?.();
  }

  simulateMessage(payload: unknown): void {
    this.onmessage?.({ data: JSON.stringify(payload) });
  }
}

describe("resolveSocketUrl", () => {
  it("derives ws URL from origin and appends the token", () => {
    const url = resolveSocketUrl("abc123");
    expect(url).toContain("/ws/dispatcher");
    expect(url).toContain("token=abc123");
    expect(url.startsWith("ws://") || url.startsWith("wss://")).toBe(true);
  });

  it("omits token when none is provided", () => {
    expect(resolveSocketUrl(null)).not.toContain("token=");
  });
});

describe("DispatcherSocketService", () => {
  let original: typeof WebSocket;

  beforeEach(() => {
    FakeWebSocket.instances = [];
    original = globalThis.WebSocket;
    (globalThis as unknown as { WebSocket: unknown }).WebSocket = FakeWebSocket;
  });

  afterEach(() => {
    (globalThis as unknown as { WebSocket: unknown }).WebSocket = original;
    vi.restoreAllMocks();
  });

  it("transitions connecting → open and delivers events", () => {
    const svc = new DispatcherSocketService();
    svc.setTokenProvider(() => "tok");

    const statuses: SocketStatus[] = [];
    const events: DispatcherEvent[] = [];
    svc.onStatus((s) => statuses.push(s));
    svc.on((e) => events.push(e));

    svc.connect();
    expect(svc.getStatus()).toBe("connecting");

    const ws = FakeWebSocket.instances[0];
    ws.simulateOpen();
    expect(svc.getStatus()).toBe("open");

    ws.simulateMessage({
      type: "incident.created",
      payload: { incident_id: "i1", number: "0001" },
    });
    expect(events).toHaveLength(1);
    expect(events[0].type).toBe("incident.created");

    // Pong frames are consumed internally, not delivered to handlers.
    ws.simulateMessage({ type: "pong" });
    expect(events).toHaveLength(1);

    svc.disconnect();
    expect(svc.getStatus()).toBe("closed");
    expect(statuses).toContain("open");
  });

  it("reconnects after an unexpected close", () => {
    vi.useFakeTimers();
    const svc = new DispatcherSocketService();
    svc.setTokenProvider(() => null);
    svc.connect();

    const first = FakeWebSocket.instances[0];
    first.simulateOpen();
    // Unexpected drop (not an explicit disconnect).
    first.close();
    expect(svc.getStatus()).toBe("reconnecting");

    // Backoff elapses → a new socket is created.
    vi.advanceTimersByTime(5_000);
    expect(FakeWebSocket.instances.length).toBeGreaterThan(1);

    svc.disconnect();
    vi.useRealTimers();
  });
});
