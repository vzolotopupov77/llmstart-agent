import { describe, expect, it } from "vitest";

import { parseSseBlocks, parseSseEvent } from "@/lib/sse-client";

const fixture = `event: reasoning
data: {"text":"Анализ запроса"}

event: tool
data: {"name":"search_knowledge_base","status":"started","title":"Поиск в базе знаний"}

event: tool
data: {"name":"search_knowledge_base","status":"done","title":"Поиск в базе знаний"}

event: message
data: {"delta":"Привет"}

event: done
data: {"session_id":"abc-123","message":"Привет"}

`;

describe("parseSseBlocks", () => {
  it("parses complete SSE blocks", () => {
    const { blocks, remainder } = parseSseBlocks(fixture);
    expect(blocks).toHaveLength(5);
    expect(remainder).toBe("");
    expect(blocks[0]).toEqual({
      event: "reasoning",
      data: '{"text":"Анализ запроса"}',
    });
  });

  it("keeps incomplete block in remainder", () => {
    const { blocks, remainder } = parseSseBlocks("event: reasoning\ndata: {");
    expect(blocks).toHaveLength(0);
    expect(remainder).toBe("event: reasoning\ndata: {");
  });
});

describe("parseSseEvent", () => {
  it("maps known events to typed payloads", () => {
    const event = parseSseEvent({
      event: "done",
      data: '{"session_id":"uuid","message":"Ответ"}',
    });

    expect(event).toEqual({
      event: "done",
      data: { session_id: "uuid", message: "Ответ" },
    });
  });

  it("returns null for unknown events", () => {
    expect(
      parseSseEvent({ event: "unknown", data: '{"foo":"bar"}' }),
    ).toBeNull();
  });
});
