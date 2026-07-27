import { describe, expect, it, beforeEach } from "vitest";
import { useNotificationStore } from "@/store/notification.store";
import { useAuthStore } from "@/store/auth.store";

describe("notification store", () => {
  it("adds and marks notifications read", () => {
    const before = useNotificationStore.getState().items.length;
    useNotificationStore.getState().add({ level: "info", title: "T", message: "M" });
    const items = useNotificationStore.getState().items;
    expect(items.length).toBe(before + 1);
    useNotificationStore.getState().markAllRead();
    expect(useNotificationStore.getState().items.every((i) => i.read)).toBe(true);
  });
});

describe("auth store", () => {
  beforeEach(() => useAuthStore.getState().clearTokens());
  it("sets and clears tokens", () => {
    useAuthStore.getState().setTokens({ accessToken: "a", refreshToken: "r" });
    expect(useAuthStore.getState().isAuthenticated).toBe(true);
    useAuthStore.getState().clearTokens();
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
  });
});
