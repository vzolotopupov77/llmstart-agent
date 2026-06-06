"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { ApiError } from "@/lib/api";
import { postChatStream } from "@/lib/sse-client";
import { waitForPlaybackGap } from "@/lib/stream-pacing";
import { usePersistedSessionId } from "@/hooks/use-persisted-session";
import { clearSessionId, getSessionId, setSessionId } from "@/lib/session";
import type {
  ChatMessage,
  ChatStreamEvent,
  MessageThinking,
  ToolStep,
} from "@/lib/types";

function createId(): string {
  return crypto.randomUUID();
}

const initialThinking = (): MessageThinking => ({
  tools: [],
  isStreaming: true,
  isResponding: false,
});

function updateAssistantMessage(
  messages: ChatMessage[],
  assistantId: string,
  updater: (message: ChatMessage) => ChatMessage,
): ChatMessage[] {
  return messages.map((message) =>
    message.id === assistantId ? updater(message) : message,
  );
}

function updateThinkingTools(
  tools: ToolStep[],
  name: string,
  title: string,
  status: ToolStep["status"],
): ToolStep[] {
  const existing = tools.find((tool) => tool.name === name);
  if (existing) {
    return tools.map((tool) =>
      tool.name === name ? { ...tool, status, title } : tool,
    );
  }
  return [...tools, { name, title, status }];
}

export function useChatStream() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const persistedSessionId = usePersistedSessionId();
  const [liveSessionId, setLiveSessionId] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const applyEvent = useCallback(
    (event: ChatStreamEvent, assistantId: string) => {
      switch (event.event) {
        case "reasoning":
          setMessages((prev) =>
            updateAssistantMessage(prev, assistantId, (message) => ({
              ...message,
              thinking: {
                ...(message.thinking ?? initialThinking()),
                isStreaming: true,
                isResponding: false,
              },
            })),
          );
          break;
        case "tool": {
          const { name, title, status } = event.data;
          setMessages((prev) =>
            updateAssistantMessage(prev, assistantId, (message) => {
              const thinking = message.thinking ?? initialThinking();
              return {
                ...message,
                thinking: {
                  ...thinking,
                  isStreaming: true,
                  tools: updateThinkingTools(
                    thinking.tools,
                    name,
                    title,
                    status,
                  ),
                },
              };
            }),
          );
          break;
        }
        case "message":
          setMessages((prev) =>
            updateAssistantMessage(prev, assistantId, (message) => ({
              ...message,
              content: message.content + event.data.delta,
              thinking: {
                ...(message.thinking ?? initialThinking()),
                isResponding: true,
                isStreaming: true,
              },
            })),
          );
          break;
        case "products":
          setMessages((prev) =>
            updateAssistantMessage(prev, assistantId, (message) => ({
              ...message,
              products: event.data.items,
            })),
          );
          break;
        case "payment_link":
          setMessages((prev) =>
            updateAssistantMessage(prev, assistantId, (message) => ({
              ...message,
              paymentLink: event.data.url,
            })),
          );
          break;
        case "done":
          setMessages((prev) =>
            updateAssistantMessage(prev, assistantId, (message) => ({
              ...message,
              content: event.data.message || message.content,
              thinking: message.thinking
                ? {
                    ...message.thinking,
                    isStreaming: false,
                    isResponding: false,
                  }
                : {
                    tools: [],
                    isStreaming: false,
                    isResponding: false,
                  },
            })),
          );
          setSessionId(event.data.session_id);
          setLiveSessionId(event.data.session_id);
          break;
        case "error":
          setError(event.data.detail);
          setMessages((prev) =>
            updateAssistantMessage(prev, assistantId, (message) => ({
              ...message,
              thinking: message.thinking
                ? {
                    ...message.thinking,
                    isStreaming: false,
                    isResponding: false,
                  }
                : undefined,
            })),
          );
          break;
      }
    },
    [],
  );

  const sendMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || isStreaming) {
        return;
      }

      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      setError(null);
      setIsStreaming(true);

      const userMessage: ChatMessage = {
        id: createId(),
        role: "user",
        content: trimmed,
      };
      const assistantId = createId();
      const assistantMessage: ChatMessage = {
        id: assistantId,
        role: "assistant",
        content: "",
        thinking: initialThinking(),
      };

      setMessages((prev) => [...prev, userMessage, assistantMessage]);

      const runStream = async (activeSessionId: string | null) => {
        let lastAppliedAt = 0;

        for await (const event of postChatStream(
          trimmed,
          activeSessionId,
          controller.signal,
        )) {
          await waitForPlaybackGap(event, lastAppliedAt);
          applyEvent(event, assistantId);
          lastAppliedAt = Date.now();
        }
      };

      try {
        const currentSessionId = getSessionId();
        try {
          await runStream(currentSessionId);
        } catch (retryErr) {
          if (
            retryErr instanceof ApiError &&
            retryErr.status === 400 &&
            currentSessionId &&
            retryErr.message.toLowerCase().includes("session")
          ) {
            clearSessionId();
            setLiveSessionId(null);
            await runStream(null);
            return;
          }
          throw retryErr;
        }
      } catch (err) {
        if (err instanceof DOMException && err.name === "AbortError") {
          return;
        }
        const detail =
          err instanceof ApiError
            ? err.message
            : err instanceof Error
              ? err.message
              : "Не удалось отправить сообщение";
        setError(detail);
      } finally {
        setIsStreaming(false);
      }
    },
    [applyEvent, isStreaming],
  );

  useEffect(() => {
    return () => {
      abortRef.current?.abort();
    };
  }, []);

  return {
    messages,
    isStreaming,
    error,
    sessionId: liveSessionId ?? persistedSessionId,
    sendMessage,
    clearError: () => setError(null),
  };
}
