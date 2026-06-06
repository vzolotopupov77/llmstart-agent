import { describe, expect, it } from "vitest";

import { formatPrice } from "@/lib/format";

describe("formatPrice", () => {
  it("formats kopecks as rubles", () => {
    expect(formatPrice(2_990_000, "RUB")).toBe("29 900 ₽");
  });

  it("uses currency code when not RUB", () => {
    expect(formatPrice(10_000, "USD")).toBe("100 USD");
  });
});
