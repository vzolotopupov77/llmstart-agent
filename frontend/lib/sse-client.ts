import { backendBaseUrl } from "@/lib/config";
import type { ChatStreamEvent, Product, ToolStatus } from "@/lib/types";
import { ApiError } from "@/lib/api";

export type SseBlock = {
  event: string;
  data: string;
};

export function parseSseBlocks(buffer: string): {
  blocks: SseBlock[];
  remainder: string;
} {
  const parts = buffer.split("\n\n");
  const remainder = parts.pop() ?? "";
  const blocks: SseBlock[] = [];

  for (const part of parts) {
    if (!part.trim()) {
      continue;
    }

    let event = "message";
    const dataLines: string[] = [];

    for (const line of part.split("\n")) {
      if (line.startsWith("event:")) {
        event = line.slice(6).trim();
      } else if (line.startsWith("data:")) {
        dataLines.push(line.slice(5).trim());
      }
    }

    if (dataLines.length > 0) {
      blocks.push({ event, data: dataLines.join("\n") });
    }
  }

  return { blocks, remainder };
}

export function parseSseEvent(block: SseBlock): ChatStreamEvent | null {
  try {
    const payload = JSON.parse(block.data) as Record<string, unknown>;

    switch (block.event) {
      case "reasoning":
        return {
          event: "reasoning",
          data: { text: String(payload.text ?? "") },
        };
      case "tool":
        return {
          event: "tool",
          data: {
            name: String(payload.name ?? ""),
            status: payload.status as ToolStatus,
            title: String(payload.title ?? ""),
          },
        };
      case "products":
        return {
          event: "products",
          data: {
            items: Array.isArray(payload.items)
              ? (payload.items as Product[])
              : [],
          },
        };
      case "message":
        return {
          event: "message",
          data: { delta: String(payload.delta ?? "") },
        };
      case "payment_link":
        return {
          event: "payment_link",
          data: { url: String(payload.url ?? "") },
        };
      case "done":
        return {
          event: "done",
          data: {
            session_id: String(payload.session_id ?? ""),
            message: String(payload.message ?? ""),
          },
        };
      case "error":
        return {
          event: "error",
          data: { detail: String(payload.detail ?? "Unknown error") },
        };
      default:
        return null;
    }
  } catch {
    return null;
  }
}

export async function* postChatStream(
  message: string,
  sessionId: string | null,
  signal?: AbortSignal,
): AsyncGenerator<ChatStreamEvent> {
  const response = await fetch(`${backendBaseUrl}/api/v1/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body: JSON.stringify({
      message,
      session_id: sessionId ?? undefined,
      channel: "web",
    }),
    signal,
  });

  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const body = (await response.json()) as { detail?: string };
      if (typeof body.detail === "string") {
        detail = body.detail;
      }
    } catch {
      // ignore parse errors
    }
    throw new ApiError(detail, response.status);
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new ApiError("Empty response body", 500);
  }

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }

    buffer += decoder.decode(value, { stream: true });
    const { blocks, remainder } = parseSseBlocks(buffer);
    buffer = remainder;

    for (const block of blocks) {
      const event = parseSseEvent(block);
      if (event) {
        yield event;
      }
    }
  }

  if (buffer.trim()) {
    const { blocks } = parseSseBlocks(`${buffer}\n\n`);
    for (const block of blocks) {
      const event = parseSseEvent(block);
      if (event) {
        yield event;
      }
    }
  }
}
