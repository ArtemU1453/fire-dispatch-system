import { describe, expect, it } from "vitest";
import { loginSchema } from "@/features/auth/loginSchema";

describe("loginSchema", () => {
  it("rejects an empty username and a short password", () => {
    const r = loginSchema.safeParse({ username: "", password: "123" });
    expect(r.success).toBe(false);
  });

  it("accepts valid credentials", () => {
    const r = loginSchema.safeParse({ username: "dispatcher", password: "secret1", remember: true });
    expect(r.success).toBe(true);
  });
});
