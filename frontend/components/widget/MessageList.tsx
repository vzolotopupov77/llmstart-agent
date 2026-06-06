"use client";

import { useEffect, useRef } from "react";

import { MessageBubble } from "@/components/widget/MessageBubble";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { ChatMessage } from "@/lib/types";

type MessageListProps = {
  messages: ChatMessage[];
};

export function MessageList({ messages }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <ScrollArea className="h-[320px] pr-3">
      <div className="flex flex-col gap-4">
        {messages.length === 0 ? (
          <p className="py-8 text-center text-sm text-zinc-500">
            Задайте вопрос о курсах — консультант подберёт программу и поможет
            с оплатой.
          </p>
        ) : null}
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  );
}
