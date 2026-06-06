"use client";

import { useState } from "react";
import { Bot } from "lucide-react";

import { ChatInput } from "@/components/widget/ChatInput";
import { MessageList } from "@/components/widget/MessageList";
import { QuickActions } from "@/components/widget/QuickActions";
import { TelegramHandoffButton } from "@/components/widget/TelegramHandoffButton";
import { useChatStream } from "@/hooks/use-chat-stream";

type ChatPanelProps = {
  className?: string;
};

export function ChatPanel({ className }: ChatPanelProps) {
  const {
    messages,
    isStreaming,
    error,
    sessionId,
    sendMessage,
    clearError,
  } = useChatStream();
  const [pendingPrompt, setPendingPrompt] = useState<string | null>(null);
  const [activeQuickAction, setActiveQuickAction] = useState<string | null>(
    null,
  );

  const handleQuickAction = (prompt: string) => {
    setActiveQuickAction(prompt);
    setPendingPrompt(prompt);
    void sendMessage(prompt);
    setPendingPrompt(null);
  };

  return (
    <div
      className={
        className ??
        "flex w-full max-w-md flex-col overflow-hidden rounded-2xl border border-cyan-500/25 bg-zinc-950/90 shadow-[0_0_48px_rgba(34,211,238,0.12)] backdrop-blur-xl"
      }
    >
      <header className="flex items-center justify-between border-b border-white/10 px-4 py-3">
        <div className="flex items-center gap-2">
          <div className="flex size-8 items-center justify-center rounded-lg bg-cyan-500/15 text-cyan-300">
            <Bot className="size-4" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-zinc-50">ИИ-Консультант</h2>
            <p className="flex items-center gap-1.5 text-xs text-zinc-400">
              <span className="size-2 rounded-full bg-emerald-400" />
              В сети
            </p>
          </div>
        </div>
      </header>

      <div className="flex flex-col gap-3 p-4">
        <MessageList messages={messages} />

        {error ? (
          <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-200">
            <div className="flex items-start justify-between gap-2">
              <span>{error}</span>
              <button
                type="button"
                onClick={clearError}
                className="text-xs text-red-300 underline"
              >
                Закрыть
              </button>
            </div>
          </div>
        ) : null}

        <QuickActions
          onSelect={handleQuickAction}
          disabled={isStreaming}
          activePrompt={activeQuickAction}
        />

        <ChatInput
          onSend={(text) => {
            setActiveQuickAction(null);
            void sendMessage(text);
          }}
          disabled={isStreaming}
          externalValue={pendingPrompt}
          onExternalValueConsumed={() => setPendingPrompt(null)}
        />

        <TelegramHandoffButton sessionId={sessionId} />
      </div>
    </div>
  );
}
