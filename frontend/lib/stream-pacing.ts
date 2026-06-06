import type { ChatStreamEvent } from "@/lib/types";

const PACING_MS: Partial<Record<ChatStreamEvent["event"], number>> = {
  reasoning: 400,
};

export function minGapBeforeEvent(event: ChatStreamEvent): number {
  switch (event.event) {
    case "tool":
      return event.data.status === "started" ? 550 : 400;
    case "message":
      return 30;
    case "products":
    case "payment_link":
      return 200;
    case "done":
    case "error":
      return 0;
    default:
      return PACING_MS[event.event] ?? 0;
  }
}

export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

export async function waitForPlaybackGap(
  event: ChatStreamEvent,
  lastAppliedAt: number,
): Promise<void> {
  const minGap = minGapBeforeEvent(event);
  if (minGap <= 0 || lastAppliedAt <= 0) {
    return;
  }

  const elapsed = Date.now() - lastAppliedAt;
  if (elapsed < minGap) {
    await sleep(minGap - elapsed);
  }
}
