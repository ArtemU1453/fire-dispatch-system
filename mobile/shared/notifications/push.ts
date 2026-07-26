// Push client (Stage 19 §Push).
//
// Provider-agnostic: the device obtains a token from whatever push transport the
// build uses (FCM, APNs, a corporate gateway) via an injected `PushTransport`,
// registers it with the backend, and routes incoming messages to handlers by
// event type. No vendor is hard-coded here.

import type { ApiClient } from "../api/client.js";

export type PushEvent =
  | "new_incident"
  | "incident_change"
  | "route_change"
  | "new_message"
  | "critical";

export interface PushMessage {
  event: PushEvent;
  title: string;
  body: string;
  data: Record<string, unknown>;
  priority: string;
}

// Abstracts the native push SDK: obtaining a token and receiving messages.
export interface PushTransport {
  getToken(): Promise<string>;
  onMessage(handler: (msg: PushMessage) => void): void;
}

export class PushClient {
  private handlers = new Map<PushEvent, ((m: PushMessage) => void)[]>();

  constructor(
    private client: ApiClient,
    private transport: PushTransport,
  ) {}

  async register(userId: string, app: string, platform: string): Promise<string> {
    const token = await this.transport.getToken();
    await this.client.registerDevice(token, userId, app, platform);
    this.transport.onMessage((msg) => this.dispatch(msg));
    return token;
  }

  on(event: PushEvent, handler: (m: PushMessage) => void): void {
    const list = this.handlers.get(event) ?? [];
    list.push(handler);
    this.handlers.set(event, list);
  }

  private dispatch(msg: PushMessage): void {
    for (const h of this.handlers.get(msg.event) ?? []) h(msg);
  }
}
