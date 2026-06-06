import { afterEach, describe, expect, it } from "vitest";

import { clearSessionId, getSessionId, setSessionId } from "@/lib/session";

describe("session storage", () => {
  afterEach(() => {
    clearSessionId();
  });

  it("stores and reads session id", () => {
    setSessionId("test-session");
    expect(getSessionId()).toBe("test-session");
  });

  it("clears session id", () => {
    setSessionId("test-session");
    clearSessionId();
    expect(getSessionId()).toBeNull();
  });
});
