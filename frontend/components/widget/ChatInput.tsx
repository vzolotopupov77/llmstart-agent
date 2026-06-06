"use client";

import { useState } from "react";
import { Send } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

type ChatInputProps = {
  onSend: (message: string) => void;
  disabled?: boolean;
  externalValue?: string | null;
  onExternalValueConsumed?: () => void;
};

export function ChatInput({
  onSend,
  disabled = false,
  externalValue = null,
  onExternalValueConsumed,
}: ChatInputProps) {
  const [value, setValue] = useState("");

  const effectiveValue = externalValue ?? value;

  const handleSubmit = () => {
    const text = effectiveValue.trim();
    if (!text || disabled) {
      return;
    }
    onSend(text);
    setValue("");
    onExternalValueConsumed?.();
  };

  return (
    <div className="flex items-end gap-2">
      <Textarea
        value={effectiveValue}
        onChange={(event) => {
          if (!externalValue) {
            setValue(event.target.value);
          }
        }}
        onKeyDown={(event) => {
          if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            handleSubmit();
          }
        }}
        placeholder="Напишите сообщение..."
        disabled={disabled}
        rows={2}
        className="min-h-[52px] flex-1"
      />
      <Button
        type="button"
        size="icon"
        onClick={handleSubmit}
        disabled={disabled || !effectiveValue.trim()}
        aria-label="Отправить"
      >
        <Send className="size-4" />
      </Button>
    </div>
  );
}
