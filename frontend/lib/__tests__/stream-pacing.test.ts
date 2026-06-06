import { describe, expect, it } from "vitest";

import { minGapBeforeEvent } from "@/lib/stream-pacing";

describe("minGapBeforeEvent", () => {
  it("uses longer gap for tool started events", () => {
    expect(
      minGapBeforeEvent({
        event: "tool",
        data: {
          name: "list_b2c_products",
          status: "started",
          title: "Каталог курсов",
        },
      }),
    ).toBeGreaterThan(
      minGapBeforeEvent({
        event: "tool",
        data: {
          name: "list_b2c_products",
          status: "done",
          title: "Каталог курсов",
        },
      }),
    );
  });

  it("does not delay done events", () => {
    expect(
      minGapBeforeEvent({
        event: "done",
        data: { session_id: "abc", message: "Ответ" },
      }),
    ).toBe(0);
  });
});
